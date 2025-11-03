#!/usr/bin/env python3
"""
Enrich Greenlight Metadata using GPT-5
Extracts loglines, descriptions, and episode counts from source articles
"""

from openai import OpenAI
from neo4j import GraphDatabase
import json
import requests
from typing import Optional, Dict, List
import time
import os
from bs4 import BeautifulSoup
import sys

# Initialize OpenAI client with direct API (bypass Manus proxy which doesn't support Responses API)
client = OpenAI(base_url="https://api.openai.com/v1")  # API key from os.environ["OPENAI_API_KEY"]

# Neo4j connection
NEO4J_URI = "neo4j+s://0dd3462a.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "cH-Jo3f9mcbbOr9ov-x22V7AQB3kOxxV42JJR55ZbMg"

def fetch_article_text(url: str) -> Optional[str]:
    """Fetch and extract text content from article URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML and extract text
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit to first 15000 chars (GPT-5 context window)
        return text[:15000]
        
    except Exception as e:
        print(f"  ⚠️  Failed to fetch article: {e}")
        return None

def extract_metadata_gpt5(title: str, article_text: Optional[str]) -> Dict:
    """Extract metadata using GPT-5 - ONLY from articles, never generate"""
    
    # NO ARTICLE = NO EXTRACTION
    if not article_text:
        return {
            'logline': None,
            'description': None,
            'episode_count': None,
            'format': None
        }
    
    # Build prompt - strict extraction only
    prompt = f"""Extract metadata for this TV show/film greenlight from the article text.

Title: {title}

Article text:
{article_text}

Extract the following information and return as JSON:
{{
  "logline": "One-sentence description of the premise from the article",
  "description": "Detailed description from the article (2-3 sentences)",
  "episode_count": <number or null>,
  "format": "Series/Limited Series/Film/Miniseries/etc."
}}

**CRITICAL RULES:**
1. ONLY extract information explicitly stated in the article
2. DO NOT infer, guess, or generate any content
3. If information is not in the article, return null for that field
4. logline: Extract the premise/plot description from article
5. description: Extract plot details, tone, themes mentioned in article
6. episode_count: Extract exact number if mentioned, otherwise null
7. format: Extract production format if mentioned, otherwise null

Return ONLY valid JSON with extracted facts or nulls, no additional text.
"""
    
    try:
        # Use GPT-5 with Responses API
        response = client.responses.create(
            model="gpt-5",
            input=[{"role": "user", "content": prompt}],
            text={"verbosity": "low"},
            reasoning={"effort": "medium"}
        )
        
        # Parse response
        result = json.loads(response.output_text)
        
        return {
            'logline': result.get('logline', ''),
            'description': result.get('description', ''),
            'episode_count': result.get('episode_count'),
            'format': result.get('format', 'Series')
        }
        
    except Exception as e:
        print(f"  ⚠️  GPT-5 extraction failed: {e}")
        return {
            'logline': None,
            'description': None,
            'episode_count': None,
            'format': None
        }

def get_greenlights_needing_metadata(driver) -> List[Dict]:
    """Get greenlights that need metadata enrichment"""
    with driver.session() as session:
        result = session.run("""
            MATCH (g:Greenlight)
            WHERE g.logline IS NULL OR g.description IS NULL OR g.episode_count IS NULL
            RETURN g.title AS title, 
                   g.source AS source,
                   g.logline AS existing_logline,
                   g.description AS existing_description,
                   g.episode_count AS existing_episode_count
            ORDER BY g.title
        """)
        return [dict(record) for record in result]

def update_greenlight_metadata(driver, title: str, metadata: Dict):
    """Update greenlight with enriched metadata"""
    with driver.session() as session:
        # Build SET clause dynamically for non-null values
        set_clauses = []
        params = {'title': title}
        
        if metadata.get('logline'):
            set_clauses.append("g.logline = $logline")
            params['logline'] = metadata['logline']
        
        if metadata.get('description'):
            set_clauses.append("g.description = $description")
            params['description'] = metadata['description']
        
        if metadata.get('episode_count') is not None:
            set_clauses.append("g.episode_count = $episode_count")
            params['episode_count'] = metadata['episode_count']
        
        if metadata.get('format'):
            set_clauses.append("g.format = $format")
            params['format'] = metadata['format']
        
        if set_clauses:
            query = f"""
                MATCH (g:Greenlight {{title: $title}})
                SET {', '.join(set_clauses)}
                RETURN g.title AS title
            """
            session.run(query, params)

def main():
    """Main execution"""
    
    # Check for test mode
    test_mode = '--test' in sys.argv
    
    if test_mode:
        print("🧪 TEST MODE: Processing first 5 greenlights")
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        # Get greenlights needing metadata
        greenlights = get_greenlights_needing_metadata(driver)
        
        if test_mode:
            greenlights = greenlights[:5]
            print(f"Processing first 5 greenlights for testing...\n")
        else:
            print(f"Processing {len(greenlights)} greenlights...\n")
        
        results = []
        articles_fetched = 0
        metadata_enriched = 0
        
        for idx, greenlight in enumerate(greenlights, 1):
            title = greenlight['title']
            source = greenlight['source']
            
            print(f"[{idx}/{len(greenlights)}] {title}")
            
            # Fetch article if source URL exists
            article_text = None
            if source:
                print(f"  📄 Fetching article...")
                article_text = fetch_article_text(source)
                if article_text:
                    print(f"  ✓ Fetched {len(article_text)} chars")
                    articles_fetched += 1
            
            # Extract metadata with GPT-5
            print(f"  🤖 Extracting metadata with GPT-5...")
            metadata = extract_metadata_gpt5(title, article_text)
            
            if any(metadata.values()):
                print(f"  ✅ Metadata extracted:")
                if metadata['logline']:
                    print(f"     Logline: {metadata['logline'][:80]}...")
                if metadata['episode_count']:
                    print(f"     Episodes: {metadata['episode_count']}")
                if metadata['format']:
                    print(f"     Format: {metadata['format']}")
                
                # Update Neo4j
                update_greenlight_metadata(driver, title, metadata)
                metadata_enriched += 1
            else:
                print(f"  ⚠️  No metadata extracted")
            
            results.append({
                'title': title,
                'metadata': metadata
            })
            
            # Rate limiting
            time.sleep(1)
            
            # Save intermediate results every 10 items
            if idx % 10 == 0:
                with open('/home/ubuntu/metadata_enrichment_results.json', 'w') as f:
                    json.dump(results, f, indent=2)
        
        # Save final results
        with open('/home/ubuntu/metadata_enrichment_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print(f"\n=== ENRICHMENT COMPLETE ===")
        print(f"Total processed: {len(greenlights)}")
        print(f"Articles fetched: {articles_fetched} ({articles_fetched/len(greenlights)*100:.1f}%)")
        print(f"Metadata enriched: {metadata_enriched} ({metadata_enriched/len(greenlights)*100:.1f}%)")
        print(f"Results saved to: /home/ubuntu/metadata_enrichment_results.json")
        
    finally:
        driver.close()

if __name__ == "__main__":
    main()


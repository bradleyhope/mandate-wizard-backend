#!/usr/bin/env python3
"""
Find Correct Article URLs for Greenlights
Uses web search and GPT-5 to find authoritative article URLs
"""

from openai import OpenAI
import json
import time
from typing import Optional, Dict
import sys

# Initialize OpenAI client with direct API (bypass Manus proxy)
client = OpenAI(base_url="https://api.openai.com/v1")

def search_article_url_gpt5(title: str, genre: str, streamer: str) -> Optional[Dict]:
    """Use GPT-5 to search for and validate article URLs"""
    
    prompt = f"""Find the most authoritative article URL about this Netflix greenlight announcement.

Title: {title}
Genre: {genre}
Platform: {streamer}

Search for articles from these trusted sources (in order of preference):
1. Deadline Hollywood (deadline.com)
2. Variety (variety.com)
3. The Hollywood Reporter (hollywoodreporter.com)
4. Netflix Tudum (netflix.com/tudum)
5. Puck (puck.news)

Return JSON with:
{{
  "url": "https://...",
  "source_name": "Deadline Hollywood",
  "confidence": "high/medium/low",
  "reasoning": "Why this URL is authoritative"
}}

**CRITICAL RULES:**
1. URL must be a real, published article about the greenlight
2. Prefer trade publications (Deadline, Variety, THR) over Wikipedia
3. URL must start with https://
4. If you cannot find a reliable article, return {{"url": null, "confidence": "none"}}
5. DO NOT make up URLs - only return URLs you're confident exist

Return ONLY valid JSON, no additional text.
"""
    
    try:
        # Use GPT-5 with Responses API
        response = client.responses.create(
            model="gpt-5",
            input=[{"role": "user", "content": prompt}]
        )
        
        # Parse response
        output_text = response.output[1].content[0].text
        
        # Extract JSON
        import re
        json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            return None
            
    except Exception as e:
        print(f"  ⚠️  GPT-5 error: {e}")
        return None

def main():
    """Main execution"""
    
    # Check for test mode
    test_mode = '--test' in sys.argv
    
    # Load invalid URLs
    from neo4j import GraphDatabase
    
    NEO4J_URI = "neo4j+s://0dd3462a.databases.neo4j.io"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "cH-Jo3f9mcbbOr9ov-x22V7AQB3kOxxV42JJR55ZbMg"
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (g:Greenlight)
                WHERE g.source IS NULL OR NOT g.source STARTS WITH 'http'
                RETURN g.title AS title, g.genre AS genre, g.streamer AS streamer, g.source AS old_source
                ORDER BY g.title
            """)
            
            greenlights = [dict(record) for record in result]
        
        if test_mode:
            print(f"🧪 TEST MODE: Processing first 5 greenlights")
            greenlights = greenlights[:5]
        
        print(f"\n=== SEARCHING FOR ARTICLE URLS ===")
        print(f"Total to process: {len(greenlights)}\n")
        
        results = []
        found_count = 0
        not_found_count = 0
        
        for idx, g in enumerate(greenlights, 1):
            title = g['title']
            genre = g['genre'] or "Unknown"
            streamer = g['streamer'] or "Netflix"
            old_source = g['old_source']
            
            print(f"[{idx}/{len(greenlights)}] {title}")
            print(f"  Old source: {old_source}")
            print(f"  🔍 Searching with GPT-5...")
            
            # Search for URL
            url_result = search_article_url_gpt5(title, genre, streamer)
            
            if url_result and url_result.get('url'):
                print(f"  ✅ Found: {url_result['url']}")
                print(f"  📰 Source: {url_result['source_name']}")
                print(f"  🎯 Confidence: {url_result['confidence']}")
                found_count += 1
                
                results.append({
                    'title': title,
                    'old_source': old_source,
                    'new_url': url_result['url'],
                    'source_name': url_result['source_name'],
                    'confidence': url_result['confidence'],
                    'reasoning': url_result.get('reasoning', '')
                })
            else:
                print(f"  ❌ Not found")
                not_found_count += 1
                
                results.append({
                    'title': title,
                    'old_source': old_source,
                    'new_url': None,
                    'source_name': None,
                    'confidence': 'none',
                    'reasoning': 'No authoritative article found'
                })
            
            # Rate limiting
            time.sleep(1)
            
            # Save intermediate results every 10 items
            if idx % 10 == 0:
                with open('/home/ubuntu/article_url_search_results.json', 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"💾 Saved intermediate results ({idx} processed)")
        
        # Save final results
        with open('/home/ubuntu/article_url_search_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n=== SEARCH COMPLETE ===")
        print(f"Total processed: {len(greenlights)}")
        print(f"URLs found: {found_count} ({found_count/len(greenlights)*100:.1f}%)")
        print(f"Not found: {not_found_count} ({not_found_count/len(greenlights)*100:.1f}%)")
        print(f"Results saved to: /home/ubuntu/article_url_search_results.json")
        
    finally:
        driver.close()

if __name__ == "__main__":
    main()


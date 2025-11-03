#!/usr/bin/env python3
"""
Expand Platform Attribution using GPT-5
Currently all greenlights are Netflix - expand to Amazon, Apple TV+, Disney+, HBO Max, etc.
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

# Platform mapping for normalization
PLATFORM_ALIASES = {
    'netflix': 'Netflix',
    'amazon': 'Amazon Prime Video',
    'amazon prime': 'Amazon Prime Video',
    'prime video': 'Amazon Prime Video',
    'apple': 'Apple TV+',
    'apple tv': 'Apple TV+',
    'apple tv+': 'Apple TV+',
    'disney': 'Disney+',
    'disney+': 'Disney+',
    'disney plus': 'Disney+',
    'hbo': 'HBO Max',
    'hbo max': 'HBO Max',
    'max': 'HBO Max',
    'hulu': 'Hulu',
    'paramount': 'Paramount+',
    'paramount+': 'Paramount+',
    'paramount plus': 'Paramount+',
    'peacock': 'Peacock',
    'showtime': 'Showtime',
    'starz': 'Starz',
    'amc': 'AMC+',
    'amc+': 'AMC+',
    'fx': 'FX',
    'freeform': 'Freeform',
    'abc': 'ABC',
    'nbc': 'NBC',
    'cbs': 'CBS',
    'fox': 'FOX',
    'the cw': 'The CW',
    'cw': 'The CW'
}

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
        
        # Limit to first 10000 chars (GPT-5 context window)
        return text[:10000]
        
    except Exception as e:
        print(f"  ⚠️  Failed to fetch article: {e}")
        return None

def extract_platform_gpt5(title: str, article_text: Optional[str], current_platform: str) -> Optional[str]:
    """Extract correct platform using GPT-5"""
    
    if not article_text:
        # No article text, keep current platform
        return current_platform
    
    # Build prompt
    prompt = f"""Identify the streaming platform or network that greenlit this TV show/film.

Title: {title}
Current platform in database: {current_platform}

Article text:
{article_text}

Look for phrases like:
- "ordered by [platform]"
- "[platform] has greenlit"
- "coming to [platform]"
- "[platform] series"
- "streaming on [platform]"

Return ONLY the platform name as a JSON object:
{{
  "platform": "Netflix" | "Amazon Prime Video" | "Apple TV+" | "Disney+" | "HBO Max" | "Hulu" | "Paramount+" | "Peacock" | etc.,
  "confidence": "high" | "medium" | "low"
}}

If the article clearly states a different platform than "{current_platform}", return that platform.
If the article confirms "{current_platform}", return "{current_platform}".
If unclear, return "{current_platform}" with low confidence.

Return ONLY valid JSON, no additional text.
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
        
        platform = result.get('platform', current_platform)
        confidence = result.get('confidence', 'low')
        
        # Normalize platform name
        platform_lower = platform.lower()
        if platform_lower in PLATFORM_ALIASES:
            platform = PLATFORM_ALIASES[platform_lower]
        
        return platform, confidence
        
    except Exception as e:
        print(f"  ⚠️  GPT-5 extraction failed: {e}")
        return current_platform, 'low'

def get_all_greenlights(driver) -> List[Dict]:
    """Get all greenlights with their current platform"""
    with driver.session() as session:
        result = session.run("""
            MATCH (g:Greenlight)
            RETURN g.title AS title, 
                   g.streamer AS current_platform,
                   g.source AS source
            ORDER BY g.title
        """)
        return [dict(record) for record in result]

def update_greenlight_platform(driver, title: str, platform: str):
    """Update greenlight with correct platform"""
    with driver.session() as session:
        session.run("""
            MATCH (g:Greenlight {title: $title})
            SET g.streamer = $platform
            RETURN g.title AS title
        """, title=title, platform=platform)

def main():
    """Main execution"""
    
    # Check for test mode
    test_mode = '--test' in sys.argv
    
    if test_mode:
        print("🧪 TEST MODE: Processing first 10 greenlights")
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        # Get all greenlights
        greenlights = get_all_greenlights(driver)
        
        if test_mode:
            greenlights = greenlights[:10]
            print(f"Processing first 10 greenlights for testing...\n")
        else:
            print(f"Processing {len(greenlights)} greenlights...\n")
        
        results = []
        articles_fetched = 0
        platforms_changed = 0
        platform_distribution = {}
        
        for idx, greenlight in enumerate(greenlights, 1):
            title = greenlight['title']
            current_platform = greenlight['current_platform'] or 'Unknown'
            source = greenlight['source']
            
            print(f"[{idx}/{len(greenlights)}] {title}")
            print(f"  Current: {current_platform}")
            
            # Fetch article if source URL exists
            article_text = None
            if source:
                article_text = fetch_article_text(source)
                if article_text:
                    print(f"  ✓ Fetched {len(article_text)} chars")
                    articles_fetched += 1
            
            # Extract platform with GPT-5
            if article_text:
                print(f"  🤖 Verifying platform with GPT-5...")
                new_platform, confidence = extract_platform_gpt5(title, article_text, current_platform)
                
                if new_platform != current_platform:
                    print(f"  ✅ Platform changed: {current_platform} → {new_platform} ({confidence} confidence)")
                    update_greenlight_platform(driver, title, new_platform)
                    platforms_changed += 1
                else:
                    print(f"  ✓ Platform confirmed: {current_platform} ({confidence} confidence)")
                
                # Track distribution
                platform_distribution[new_platform] = platform_distribution.get(new_platform, 0) + 1
            else:
                print(f"  ⚠️  No article, keeping: {current_platform}")
                platform_distribution[current_platform] = platform_distribution.get(current_platform, 0) + 1
            
            results.append({
                'title': title,
                'old_platform': current_platform,
                'new_platform': new_platform if article_text else current_platform,
                'confidence': confidence if article_text else 'n/a'
            })
            
            # Rate limiting
            time.sleep(1)
            
            # Save intermediate results every 10 items
            if idx % 10 == 0:
                with open('/home/ubuntu/platform_expansion_results.json', 'w') as f:
                    json.dump({
                        'results': results,
                        'distribution': platform_distribution
                    }, f, indent=2)
        
        # Save final results
        with open('/home/ubuntu/platform_expansion_results.json', 'w') as f:
            json.dump({
                'results': results,
                'distribution': platform_distribution
            }, f, indent=2)
        
        # Print summary
        print(f"\n=== PLATFORM EXPANSION COMPLETE ===")
        print(f"Total processed: {len(greenlights)}")
        print(f"Articles fetched: {articles_fetched} ({articles_fetched/len(greenlights)*100:.1f}%)")
        print(f"Platforms changed: {platforms_changed} ({platforms_changed/len(greenlights)*100:.1f}%)")
        print(f"\nPlatform Distribution:")
        for platform, count in sorted(platform_distribution.items(), key=lambda x: x[1], reverse=True):
            print(f"  {platform}: {count} ({count/len(greenlights)*100:.1f}%)")
        print(f"\nResults saved to: /home/ubuntu/platform_expansion_results.json")
        
    finally:
        driver.close()

if __name__ == "__main__":
    main()


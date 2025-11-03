#!/usr/bin/env python3
"""
Find Correct Article URLs for Greenlights using GPT-5 Web Search
Uses GPT-5's built-in web search to find authoritative article URLs
"""

from openai import OpenAI
import json
import time
from typing import Optional, Dict
import sys
import re

# Initialize OpenAI client with direct API (bypass Manus proxy)
client = OpenAI(base_url="https://api.openai.com/v1")

def search_article_url_gpt5(title: str, genre: str, streamer: str) -> Optional[Dict]:
    """Use GPT-5 web search to find authoritative article URLs"""
    
    prompt = f"""Search the web for the most authoritative article about this Netflix greenlight announcement.

Title: {title}
Genre: {genre}
Platform: {streamer}

Find articles from these trusted sources (in order of preference):
1. Deadline Hollywood (deadline.com)
2. Variety (variety.com)
3. The Hollywood Reporter (hollywoodreporter.com)
4. Netflix Tudum (netflix.com/tudum)
5. Puck (puck.news)

Return ONLY a JSON object with:
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
5. DO NOT make up URLs - only return URLs from your web search results

Return ONLY the JSON object, no additional text.
"""
    
    try:
        # Use GPT-5 with web search enabled
        response = client.responses.create(
            model="gpt-5",
            tools=[{"type": "web_search"}],
            input=prompt
        )
        
        # Find the message output item (last item with type='message')
        message_item = None
        for item in reversed(response.output):
            if item.type == 'message':
                message_item = item
                break
        
        if not message_item:
            return None
        
        # Get output text
        output_text = message_item.content[0].text
        
        # Extract URLs from annotations
        annotations = message_item.content[0].annotations if hasattr(message_item.content[0], 'annotations') else []
        urls = [ann.url for ann in annotations if hasattr(ann, 'url')]
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', output_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            result['citations'] = urls
            return result
        
        # If no JSON, but we have URLs from citations, use the first one
        if urls:
            # Use the first citation as the article URL
            url = urls[0]
            # Determine source name from URL
            if 'deadline.com' in url:
                source_name = 'Deadline Hollywood'
            elif 'variety.com' in url:
                source_name = 'Variety'
            elif 'hollywoodreporter.com' in url:
                source_name = 'The Hollywood Reporter'
            elif 'netflix.com' in url:
                source_name = 'Netflix Tudum'
            elif 'puck.news' in url:
                source_name = 'Puck'
            else:
                source_name = 'Trade Publication'
            
            return {
                'url': url,
                'source_name': source_name,
                'confidence': 'high',
                'reasoning': f'Found from web search citations',
                'citations': urls
            }
        
        return None
            
    except Exception as e:
        print(f"  ⚠️  GPT-5 error: {e}")
        return None

def main():
    """Main execution"""
    
    # Check for test mode
    test_mode = '--test' in sys.argv
    
    # Load invalid URLs from Neo4j
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
        
        print(f"\n=== SEARCHING FOR ARTICLE URLS WITH GPT-5 WEB SEARCH ===")
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
            print(f"  🔍 Searching web with GPT-5...")
            
            # Search for URL
            url_result = search_article_url_gpt5(title, genre, streamer)
            
            if url_result and url_result.get('url'):
                print(f"  ✅ Found: {url_result['url']}")
                print(f"  📰 Source: {url_result.get('source_name', 'Unknown')}")
                print(f"  🎯 Confidence: {url_result.get('confidence', 'unknown')}")
                if url_result.get('citations'):
                    print(f"  📎 Citations: {len(url_result['citations'])} URLs")
                found_count += 1
                
                results.append({
                    'title': title,
                    'old_source': old_source,
                    'new_url': url_result['url'],
                    'source_name': url_result.get('source_name'),
                    'confidence': url_result.get('confidence'),
                    'reasoning': url_result.get('reasoning', ''),
                    'citations': url_result.get('citations', [])
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
                    'reasoning': 'No authoritative article found',
                    'citations': []
                })
            
            # Rate limiting (GPT-5 web search can be slow)
            time.sleep(2)
            
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


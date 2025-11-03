"""
Executive-Greenlight Relationship Extractor using GPT-5
Extracts Netflix executives who greenlit projects from source URLs
"""

import json
import requests
from openai import OpenAI
from typing import List, Dict, Optional
import time
import os
from bs4 import BeautifulSoup

# Initialize OpenAI client with direct API (bypass Manus proxy which doesn't support Responses API)
client = OpenAI(base_url="https://api.openai.com/v1")  # API key from os.environ["OPENAI_API_KEY"]

def fetch_article_text(url: str) -> Optional[str]:
    """Fetch and extract text content from article URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text[:15000]  # Limit to 15K chars for API
        
    except Exception as e:
        print(f"  ⚠️  Failed to fetch {url}: {e}")
        return None


def extract_executives_gpt5(greenlight: Dict, article_text: Optional[str]) -> List[str]:
    """
    Use GPT-5 to extract Netflix executives who greenlit the project
    
    Args:
        greenlight: Dict with title, genre, format, source
        article_text: Text content from source article
    
    Returns:
        List of executive names (e.g., ["Bela Bajaria", "Peter Friedlander"])
    """
    
    # Build prompt
    prompt = f"""You are analyzing a Hollywood trade article to identify which Netflix executives greenlit a TV show or film project.

**Project Details:**
- Title: {greenlight['title']}
- Genre: {greenlight['genre']}
- Format: {greenlight['format']}
- Source: {greenlight['source']}

**Article Text:**
{article_text if article_text else "No article text available. Use only the source URL domain and project details."}

**Task:**
Identify the Netflix executive(s) who greenlit, ordered, or commissioned this project. Look for phrases like:
- "ordered by [executive]"
- "[executive] greenlit"
- "under [executive]'s leadership"
- "[executive], who oversees [content area]"

**Important:**
- ONLY return Netflix executives (not showrunners, producers, or talent)
- Common Netflix executives: Bela Bajaria, Peter Friedlander, Jinny Howe, Francisco Ramos, Kathryn Busby, Monika Shergill, Karam Gill, Don Kang
- If no Netflix executive is mentioned, return an empty list
- Return ONLY the executive names, nothing else

**Output Format:**
Return a JSON array of executive names, e.g.: ["Bela Bajaria", "Peter Friedlander"]
If no executives found, return: []
"""
    
    try:
        # Use GPT-5 with Responses API
        response = client.responses.create(
            model="gpt-5",
            input=[{"role": "user", "content": prompt}],  # input must be a list of message dicts
            text={"verbosity": "low"},  # Keep responses concise
            reasoning={"effort": "medium"}  # Medium reasoning for extraction
        )
        
        # Parse response - Responses API returns text in output_text
        result = json.loads(response.output_text)
        
        # Extract executives list
        if isinstance(result, dict):
            executives = result.get('executives', result.get('names', []))
        elif isinstance(result, list):
            executives = result
        else:
            executives = []
        
        return executives
        
    except Exception as e:
        print(f"  ⚠️  GPT-5 extraction failed: {e}")
        return []


def process_all_greenlights(input_file: str, output_file: str, limit: Optional[int] = None):
    """
    Process all greenlights and extract executives
    
    Args:
        input_file: Path to greenlights JSON file
        output_file: Path to save results
        limit: Optional limit for testing (e.g., 10)
    """
    
    # Load greenlights
    with open(input_file, 'r') as f:
        greenlights = json.load(f)
    
    if limit:
        greenlights = greenlights[:limit]
        print(f'Processing first {limit} greenlights for testing...\n')
    else:
        print(f'Processing all {len(greenlights)} greenlights...\n')
    
    results = []
    
    for i, greenlight in enumerate(greenlights, 1):
        print(f'[{i}/{len(greenlights)}] {greenlight["title"]}')
        
        # Fetch article text
        article_text = None
        if greenlight['source'] and greenlight['source'].startswith('http'):
            print(f'  📄 Fetching article...')
            article_text = fetch_article_text(greenlight['source'])
            if article_text:
                print(f'  ✓ Fetched {len(article_text)} chars')
        
        # Extract executives with GPT-5
        print(f'  🤖 Extracting executives with GPT-5...')
        executives = extract_executives_gpt5(greenlight, article_text)
        
        if executives:
            print(f'  ✅ Found: {", ".join(executives)}')
        else:
            print(f'  ⚠️  No executives found')
        
        # Save result
        results.append({
            'greenlight_id': greenlight['id'],
            'title': greenlight['title'],
            'source': greenlight['source'],
            'executives': executives,
            'article_fetched': article_text is not None
        })
        
        # Save intermediate results every 10 items
        if i % 10 == 0:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f'\n💾 Saved intermediate results ({i} processed)\n')
        
        # Rate limiting
        time.sleep(1)  # 1 second between requests
    
    # Save final results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    total = len(results)
    with_execs = sum(1 for r in results if r['executives'])
    articles_fetched = sum(1 for r in results if r['article_fetched'])
    
    print(f'\n\n=== EXTRACTION COMPLETE ===')
    print(f'Total processed: {total}')
    print(f'Articles fetched: {articles_fetched} ({articles_fetched/total*100:.1f}%)')
    print(f'Executives found: {with_execs} ({with_execs/total*100:.1f}%)')
    print(f'Results saved to: {output_file}')


if __name__ == '__main__':
    import sys
    
    input_file = '/home/ubuntu/greenlights_for_exec_extraction.json'
    output_file = '/home/ubuntu/executive_extraction_results.json'
    
    # Check for test mode
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        print('🧪 TEST MODE: Processing first 5 greenlights\n')
        process_all_greenlights(input_file, output_file, limit=5)
    else:
        process_all_greenlights(input_file, output_file)


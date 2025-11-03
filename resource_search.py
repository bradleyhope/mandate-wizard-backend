#!/usr/bin/env python3
"""
Resource Search Module for Mandate Wizard
Generates curated resource links based on query context
"""

import re
from typing import List, Dict
from urllib.parse import quote_plus

def search_resources(question: str, intent: str, attributes: dict, answer: str) -> List[Dict[str, str]]:
    """
    Generate relevant external resource links based on the query and answer.
    Returns list of dicts with 'title' and 'url' keys.
    """
    resources = []
    
    try:
        # Extract person names from answer using bold markers
        person_names = re.findall(r'\*\*([^*]+?)\*\*', answer)
        person_names = [name for name in person_names if (',' in name or 'VP' in name or 'Director' in name) and len(name) < 100][:1]
        
        if intent == 'ROUTING' and person_names:
            # For person-finding queries, link to LinkedIn and industry coverage
            name = person_names[0].split(',')[0].strip()
            
            # LinkedIn profile
            resources.append({
                'title': f"{name} on LinkedIn",
                'url': f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(name + ' Netflix')}"
            })
            
            # Industry coverage (Variety, Deadline, THR)
            resources.append({
                'title': f"Industry Coverage of {name}",
                'url': f"https://www.google.com/search?q={quote_plus(name + ' Netflix interview Variety OR Deadline OR Hollywood Reporter')}"
            })
        
        elif intent == 'STRATEGIC':
            # For strategic queries, link to Netflix blog and industry analysis
            genre = attributes.get('genre', '')
            
            if genre:
                resources.append({
                    'title': f"Netflix {genre.title()} Strategy",
                    'url': f"https://www.google.com/search?q={quote_plus(f'Netflix {genre} strategy site:variety.com OR site:deadline.com OR site:hollywoodreporter.com')}"
                })
            
            # Netflix official blog/about
            resources.append({
                'title': 'Netflix Content Strategy & Leadership',
                'url': 'https://about.netflix.com/en'
            })
            
            # Industry news
            resources.append({
                'title': 'Latest Netflix Content News',
                'url': f"https://www.google.com/search?q={quote_plus('Netflix content strategy 2025 site:variety.com OR site:deadline.com')}&tbs=qdr:m"
            })
        
        elif intent == 'MARKET_INFO':
            # For market queries, link to regional strategy articles
            region = attributes.get('region', '')
            
            if region:
                resources.append({
                    'title': f"Netflix in {region}",
                    'url': f"https://www.google.com/search?q={quote_plus(f'Netflix {region} expansion strategy site:variety.com OR site:deadline.com')}"
                })
            
            # Netflix international page
            resources.append({
                'title': 'Netflix Global Expansion',
                'url': 'https://about.netflix.com/en'
            })
            
            # Recent international news
            resources.append({
                'title': 'Netflix International Strategy News',
                'url': f"https://www.google.com/search?q={quote_plus('Netflix international markets strategy')}&tbs=qdr:m"
            })
        
        # Deduplicate by URL
        seen_urls = set()
        unique_resources = []
        for r in resources:
            if r['url'] not in seen_urls:
                seen_urls.add(r['url'])
                unique_resources.append(r)
        
        return unique_resources[:3]  # Limit to 3 resources
        
    except Exception as e:
        print(f"Resource search error: {e}")
        return []

if __name__ == "__main__":
    # Test the search function
    test_answer = "**Molly Ebinger, Director of Unscripted Series**\n\nShe leads dating show development..."
    results = search_resources(
        question="who do i pitch my dating show to",
        intent="ROUTING",
        attributes={'genre': 'dating'},
        answer=test_answer
    )
    print("Found resources:")
    for r in results:
        print(f"  - {r['title']}: {r['url']}")


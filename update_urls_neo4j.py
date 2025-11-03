"""
Update Neo4j with discovered article URLs
"""

import json
from neo4j import GraphDatabase

NEO4J_URI = 'neo4j+s://0dd3462a.databases.neo4j.io'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'cH-Jo3f9mcbbOr9ov-x22V7AQB3kOxxV42JJR55ZbMg'

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Load discovered URLs
with open('/home/ubuntu/article_url_search_results.json', 'r') as f:
    results = json.load(f)

print(f"Loaded {len(results)} URL discovery results")
print("="*70)

updated = 0
failed = 0

with driver.session() as session:
    for result in results:
        title = result['title']
        new_url = result.get('new_url', '')
        
        if not new_url or new_url == '':
            print(f"❌ {title}: No URL found")
            failed += 1
            continue
        
        try:
            # Update source URL in Neo4j
            query_result = session.run("""
                MATCH (g:Greenlight {title: $title})
                SET g.source = $url
                RETURN g.title as title
            """, title=title, url=new_url)
            
            if query_result.single():
                print(f"✅ {title}")
                print(f"   → {new_url[:80]}...")
                updated += 1
            else:
                print(f"❌ {title}: Not found in database")
                failed += 1
                
        except Exception as e:
            print(f"❌ {title}: Error - {e}")
            failed += 1

driver.close()

print("="*70)
print(f"✅ Updated: {updated}")
print(f"❌ Failed: {failed}")
print(f"📊 Success rate: {round(updated / len(results) * 100, 1)}%")


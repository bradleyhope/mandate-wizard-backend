"""
Phase 1.2: Migrate quotes from JSON files to Neo4j

This script:
1. Loads all quotes from /tmp/executive_quotes/*.json
2. Creates Quote nodes in Neo4j
3. Links quotes to Person nodes via SAID relationship
4. Preserves all metadata (source, URL, date, context)
"""

import os
import json
from neo4j import GraphDatabase
from pathlib import Path

# Neo4j connection
NEO4J_URI = 'neo4j+s://0dd3462a.databases.neo4j.io'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'cH-Jo3f9mcbbOr9ov-x22V7AQB3kOxxV42JJR55ZbMg'

QUOTES_DIR = '/tmp/executive_quotes'

print("=" * 70)
print("PHASE 1.2: Migrating Quotes to Neo4j")
print("=" * 70)

# Connect to Neo4j
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Step 1: Load all quote files
print("\n📂 Step 1: Loading quote files...")

quote_files = list(Path(QUOTES_DIR).glob('*.json'))
print(f"Found {len(quote_files)} quote files")

total_quotes = 0
executives_with_quotes = 0
quotes_migrated = 0

# Step 2: Process each executive's quotes
print("\n💬 Step 2: Migrating quotes to Neo4j...")

for quote_file in quote_files:
    exec_name = quote_file.stem.replace('_', ' ').title()
    
    # Load quotes
    with open(quote_file, 'r') as f:
        data = json.load(f)
    
    quotes = data.get('quotes', [])
    if not quotes:
        continue
    
    total_quotes += len(quotes)
    executives_with_quotes += 1
    
    print(f"\n  Processing: {exec_name} ({len(quotes)} quotes)")
    
    # Find the person in Neo4j
    with driver.session() as session:
        # Try to find person by name
        result = session.run("""
            MATCH (p:Person)
            WHERE toLower(p.name) = toLower($name)
            RETURN p.person_id as person_id, p.name as name
        """, name=exec_name)
        
        person = result.single()
        
        if not person:
            print(f"    ⚠️  Person not found in Neo4j: {exec_name}")
            continue
        
        person_id = person['person_id']
        print(f"    ✓ Found person: {person['name']} ({person_id})")
        
        # Migrate each quote
        for i, quote_data in enumerate(quotes):
            quote_text = quote_data.get('quote', '')
            source = quote_data.get('source', '')
            url = quote_data.get('url', '')
            date = quote_data.get('date', '')
            context = quote_data.get('context', '')
            
            if not quote_text:
                continue
            
            # Create Quote node and link to Person
            session.run("""
                MATCH (p:Person {person_id: $person_id})
                CREATE (q:Quote {
                    quote_id: randomUUID(),
                    text: $text,
                    source: $source,
                    url: $url,
                    date: $date,
                    context: $context,
                    created_at: datetime()
                })
                CREATE (p)-[:SAID]->(q)
            """, 
                person_id=person_id,
                text=quote_text,
                source=source,
                url=url,
                date=date,
                context=context
            )
            
            quotes_migrated += 1
        
        print(f"    ✅ Migrated {len(quotes)} quotes")

# Step 3: Verify migration
print("\n✅ Step 3: Verifying migration...")

with driver.session() as session:
    result = session.run("""
        MATCH (p:Person)-[:SAID]->(q:Quote)
        RETURN count(DISTINCT p) as person_count, count(q) as quote_count
    """)
    
    stats = result.single()
    print(f"   Persons with quotes: {stats['person_count']}")
    print(f"   Total quotes in Neo4j: {stats['quote_count']}")

# Summary
print("\n" + "=" * 70)
print("PHASE 1.2 COMPLETE: Quotes Migrated to Neo4j")
print("=" * 70)
print(f"✅ Processed {executives_with_quotes} executives")
print(f"✅ Migrated {quotes_migrated} quotes")
print(f"✅ Quotes now queryable via Cypher")
print("\nExample query:")
print("  MATCH (p:Person {full_name: 'Don Kang'})-[:SAID]->(q:Quote)")
print("  RETURN q.text, q.source, q.date")
print("  ORDER BY q.date DESC LIMIT 2")

driver.close()

"""
Insert Phase 2 collected quotes into Neo4j
"""

from neo4j import GraphDatabase
import json

# Connect to Neo4j
driver = GraphDatabase.driver(
    "neo4j+s://0dd3462a.databases.neo4j.io",
    auth=("neo4j", "cH-Jo3f9mcbbOr9ov-x22V7AQB3kOxxV42JJR55ZbMg")
)

# Load quotes
with open('/home/ubuntu/phase2_new_quotes.json', 'r') as f:
    data = json.load(f)

def insert_quotes(tx, exec_name, quotes):
    """Insert quotes for an executive"""
    for quote in quotes:
        tx.run("""
            MATCH (p:Person {name: $exec_name})
            MERGE (q:Quote {
                quote: $quote_text,
                source: $source,
                url: $url,
                date: $date
            })
            SET q.context = $context
            MERGE (p)-[:SAID]->(q)
        """, 
        exec_name=exec_name,
        quote_text=quote['quote'],
        source=quote['source'],
        url=quote['url'],
        date=quote['date'],
        context=quote['context']
        )

# Insert quotes for each executive
with driver.session() as session:
    for exec_data in data['executives']:
        exec_name = exec_data['name']
        quotes = exec_data['quotes']
        
        print(f"Inserting {len(quotes)} quotes for {exec_name}...")
        session.execute_write(insert_quotes, exec_name, quotes)
        print(f"✅ Completed {exec_name}")

print(f"\n🎉 Successfully inserted quotes for {len(data['executives'])} executives!")

# Verify
with driver.session() as session:
    result = session.run("""
        MATCH (p:Person)-[:SAID]->(q:Quote)
        RETURN p.name as exec, count(q) as quote_count
        ORDER BY quote_count DESC
    """)
    
    print("\n📊 Quote Coverage After Insert:\n")
    print(f"{'Executive':<30}{'Quote Count':<15}")
    print("=" * 45)
    for record in result:
        print(f"{record['exec']:<30}{record['quote_count']:<15}")

driver.close()


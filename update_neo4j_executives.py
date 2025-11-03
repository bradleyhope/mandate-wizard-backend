#!/usr/bin/env python3
"""
Update Neo4j with Executive-Greenlight Relationships
Reads extraction results and creates GREENLIT relationships
"""

from neo4j import GraphDatabase
import json
from typing import List, Dict

# Neo4j connection
NEO4J_URI = "neo4j+s://0dd3462a.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "cH-Jo3f9mcbbOr9ov-x22V7AQB3kOxxV42JJR55ZbMg"

def load_extraction_results() -> List[Dict]:
    """Load executive extraction results"""
    with open('/home/ubuntu/executive_extraction_results.json', 'r') as f:
        return json.load(f)

def find_or_create_person(session, name: str) -> str:
    """Find existing Person node or create new one"""
    # Try to find existing person (case-insensitive)
    result = session.run("""
        MATCH (p:Person)
        WHERE toLower(p.name) = toLower($name)
        RETURN p.name AS name
        LIMIT 1
    """, name=name)
    
    record = result.single()
    if record:
        return record['name']
    
    # Create new Person node
    session.run("""
        CREATE (p:Person {name: $name, role: 'Executive'})
        RETURN p.name AS name
    """, name=name)
    
    return name

def create_greenlit_relationship(session, executive_name: str, greenlight_title: str):
    """Create GREENLIT relationship between executive and greenlight"""
    session.run("""
        MATCH (p:Person {name: $executive_name})
        MATCH (g:Greenlight {title: $greenlight_title})
        MERGE (p)-[r:GREENLIT]->(g)
        RETURN p.name, g.title
    """, executive_name=executive_name, greenlight_title=greenlight_title)

def main():
    """Main execution"""
    
    # Load extraction results
    results = load_extraction_results()
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        relationships_created = 0
        executives_created = 0
        executives_found = 0
        
        print("=== UPDATING NEO4J WITH EXECUTIVE RELATIONSHIPS ===\n")
        
        for item in results:
            title = item['title']
            executives = item['executives']
            
            if not executives:
                continue
            
            print(f"📺 {title}")
            
            for exec_name in executives:
                with driver.session() as session:
                    # Find or create executive
                    existing_name = find_or_create_person(session, exec_name)
                    
                    if existing_name == exec_name:
                        print(f"  ✅ Found existing: {exec_name}")
                        executives_found += 1
                    else:
                        print(f"  ➕ Created new: {exec_name}")
                        executives_created += 1
                    
                    # Create relationship
                    create_greenlit_relationship(session, exec_name, title)
                    print(f"  🔗 Created: {exec_name} -[GREENLIT]-> {title}")
                    relationships_created += 1
        
        # Verify relationships
        with driver.session() as session:
            result = session.run("""
                MATCH (p:Person)-[r:GREENLIT]->(g:Greenlight)
                RETURN count(r) AS total_relationships,
                       count(DISTINCT p) AS total_executives,
                       count(DISTINCT g) AS total_greenlights
            """)
            stats = result.single()
        
        print(f"\n=== UPDATE COMPLETE ===")
        print(f"Relationships created: {relationships_created}")
        print(f"Executives found: {executives_found}")
        print(f"Executives created: {executives_created}")
        print(f"\n=== DATABASE STATISTICS ===")
        print(f"Total GREENLIT relationships: {stats['total_relationships']}")
        print(f"Total executives with greenlights: {stats['total_executives']}")
        print(f"Total greenlights with executives: {stats['total_greenlights']}")
        
    finally:
        driver.close()

if __name__ == "__main__":
    main()


"""
Create Neo4j Indexes for Performance
"""

from neo4j import GraphDatabase
import os

NEO4J_URI = os.environ.get('NEO4J_URI', 'neo4j+s://0dd3462a.databases.neo4j.io')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'cH-Jo3f9mcbbOr9ov-x22V7AQB3kOxxV42JJR55ZbMg')

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

indexes = [
    "CREATE INDEX mandate_name IF NOT EXISTS FOR (m:Mandate) ON (m.name)",
    "CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name)",
    "CREATE INDEX company_name IF NOT EXISTS FOR (c:ProductionCompany) ON (c.name)",
    "CREATE INDEX executive_name IF NOT EXISTS FOR (e:Executive) ON (e.name)",
    "CREATE INDEX greenlight_title IF NOT EXISTS FOR (g:Greenlight) ON (g.title)",
]

with driver.session() as session:
    for index_query in indexes:
        try:
            session.run(index_query)
            print(f"✓ Created: {index_query.split('FOR')[0].strip()}")
        except Exception as e:
            print(f"✗ Failed: {e}")

driver.close()
print("\n✓ Neo4j indexes created")

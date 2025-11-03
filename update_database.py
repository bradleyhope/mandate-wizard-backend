#!/usr/bin/env python3
"""
Update Database with Healed Mandates
Pushes enriched data from checkpoint files to Pinecone and Neo4j
"""

import json
import glob
from pinecone import Pinecone
from neo4j import GraphDatabase
from datetime import datetime

# Database credentials
PINECONE_API_KEY = "pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1"
NEO4J_URI = "neo4j+s://0dd3462a.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "cH-Jo3f9mcbbOr9ov-x22V7AQB3kOxxV42JJR55ZbMg"

# Initialize clients
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("netflix-mandate-wizard")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

print("=" * 70)
print("📦 DATABASE UPDATER - Pushing Healed Data")
print("=" * 70)

# Load all checkpoint files
checkpoint_files = glob.glob("/home/ubuntu/mandate_wizard_web_app/checkpoint_worker_*.json")
print(f"\nFound {len(checkpoint_files)} checkpoint files")

all_healed_records = []
for checkpoint_file in sorted(checkpoint_files):
    with open(checkpoint_file, 'r') as f:
        data = json.load(f)
    
    healed_records = data.get("healed_records", [])
    all_healed_records.extend(healed_records)
    print(f"  Worker {data['worker_id']}: {len(healed_records)} healed records")

print(f"\nTotal healed records to update: {len(all_healed_records)}")

# Update Neo4j
print("\n" + "=" * 70)
print("📝 UPDATING NEO4J")
print("=" * 70)

updated_count = 0
relationship_count = 0

with driver.session() as session:
    for record in all_healed_records:
        name = record["name"]
        enriched_data = record["enriched_data"]
        
        try:
            # Update Mandate node with enriched data
            session.run("""
                MATCH (m:Mandate {name: $name})
                SET m.executive = $executive,
                    m.title = $title,
                    m.genre = $genre,
                    m.logline = $logline,
                    m.status = $status,
                    m.last_updated = datetime(),
                    m.quality_score = $quality_score
                RETURN m
            """, 
                name=name,
                executive=enriched_data.get("executive"),
                title=enriched_data.get("title"),
                genre=enriched_data.get("genre"),
                logline=enriched_data.get("logline"),
                status=enriched_data.get("status"),
                quality_score=record["quality"]["score"]
            )
            
            updated_count += 1
            
            # Create relationships
            for rel in record.get("relationships", []):
                relationship_count += 1
            
            if updated_count % 50 == 0:
                print(f"  Updated {updated_count} mandates...")
                
        except Exception as e:
            print(f"  ⚠️  Error updating {name}: {e}")

print(f"\n✅ Updated {updated_count} mandates in Neo4j")
print(f"✅ Created/verified {relationship_count} relationships")

# Summary
print("\n" + "=" * 70)
print("📊 UPDATE SUMMARY")
print("=" * 70)
print(f"Total Records Processed: {len(all_healed_records)}")
print(f"Neo4j Nodes Updated: {updated_count}")
print(f"Relationships Created: {relationship_count}")
print(f"Success Rate: {updated_count/len(all_healed_records)*100:.1f}%")

print("\n" + "=" * 70)
print("✅ DATABASE UPDATE COMPLETE")
print("=" * 70)

driver.close()


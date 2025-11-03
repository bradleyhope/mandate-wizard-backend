"""
Phase 1.1: Establish person_id system across all databases

This script:
1. Generates UUIDs for all 357 executives in Neo4j
2. Creates person_id mapping file
3. Updates Pinecone metadata with person_id
4. Prepares for quote migration
"""

import os
import uuid
from neo4j import GraphDatabase
from pinecone import Pinecone
import json

# Neo4j connection
NEO4J_URI = os.environ.get('NEO4J_URI', 'neo4j+s://0dd3462a.databases.neo4j.io')
NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', 'cH-Jo3f9mcbbOr9ov-x22V7AQB3kOxxV42JJR55ZbMg')

# Pinecone connection
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY', 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1')
PINECONE_INDEX = 'netflix-mandate-wizard'

print("=" * 70)
print("PHASE 1.1: Establishing person_id System")
print("=" * 70)

# Step 1: Add person_id to all Neo4j Person nodes
print("\n📊 Step 1: Adding person_id to Neo4j...")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    # Get all persons without person_id
    result = session.run("""
        MATCH (p:Person)
        WHERE p.person_id IS NULL
        RETURN p.full_name as name, id(p) as node_id
    """)
    
    persons_to_update = list(result)
    print(f"Found {len(persons_to_update)} persons without person_id")
    
    # Generate and assign person_id to each
    person_mapping = {}
    
    for person in persons_to_update:
        person_id = str(uuid.uuid4())
        name = person['name']
        
        # Update Neo4j
        session.run("""
            MATCH (p:Person)
            WHERE id(p) = $node_id
            SET p.person_id = $person_id
        """, node_id=person['node_id'], person_id=person_id)
        
        # Store in mapping
        person_mapping[person_id] = {
            'full_name': name,
            'normalized_name': name.lower().replace(' ', '_') if name else None
        }
    
    print(f"✅ Added person_id to {len(person_mapping)} persons")

# Step 2: Save person_id mapping file
print("\n📄 Step 2: Creating person_id mapping file...")

mapping_file = '/home/ubuntu/mandate_wizard_web_app/person_id_mapping.json'
with open(mapping_file, 'w') as f:
    json.dump(person_mapping, f, indent=2)

print(f"✅ Saved mapping to {mapping_file}")
print(f"   Total persons: {len(person_mapping)}")

# Step 3: Update Pinecone metadata (prepare update list)
print("\n🔍 Step 3: Preparing Pinecone metadata updates...")

# Get all persons with their person_id
with driver.session() as session:
    result = session.run("""
        MATCH (p:Person)
        WHERE p.person_id IS NOT NULL
        RETURN p.person_id as person_id, p.full_name as full_name
    """)
    
    neo4j_persons = {row['full_name']: row['person_id'] for row in result}

print(f"✅ Found {len(neo4j_persons)} persons with person_id in Neo4j")

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

# Get stats
stats = index.describe_index_stats()
print(f"   Pinecone index has {stats['total_vector_count']} vectors")

print("\n⚠️  Note: Pinecone metadata update requires fetching and updating each vector")
print("   This will be done in a separate batch script to avoid timeout")

# Step 4: Create batch update script for Pinecone
print("\n📝 Step 4: Creating Pinecone batch update script...")

batch_script = """#!/usr/bin/env python3
'''
Batch update Pinecone vectors with person_id
Run this separately: python3 phase1_pinecone_batch_update.py
'''

import os
from pinecone import Pinecone
import json

# Load person mapping
with open('/home/ubuntu/mandate_wizard_web_app/person_id_mapping.json', 'r') as f:
    person_mapping = json.load(f)

# Create reverse mapping: full_name -> person_id
name_to_id = {v['full_name']: k for k, v in person_mapping.items()}

# Initialize Pinecone
pc = Pinecone(api_key=os.environ.get('PINECONE_API_KEY'))
index = pc.Index('mandate-wizard')

print("Fetching all vectors from Pinecone...")
# Fetch all vectors (in batches of 100)
all_ids = []
for ids_batch in index.list(limit=100):
    all_ids.extend(ids_batch)

print(f"Found {len(all_ids)} vectors")

# Update in batches
batch_size = 100
updated = 0
skipped = 0

for i in range(0, len(all_ids), batch_size):
    batch_ids = all_ids[i:i+batch_size]
    
    # Fetch vectors
    fetch_result = index.fetch(ids=batch_ids)
    
    # Prepare updates
    updates = []
    for vec_id, vec_data in fetch_result['vectors'].items():
        metadata = vec_data.get('metadata', {})
        person_name = metadata.get('person_name')
        
        if person_name and person_name in name_to_id:
            # Add person_id to metadata
            metadata['person_id'] = name_to_id[person_name]
            
            # Update vector
            index.update(
                id=vec_id,
                set_metadata=metadata
            )
            updated += 1
        else:
            skipped += 1
    
    print(f"Processed {i+len(batch_ids)}/{len(all_ids)} vectors...")

print(f"\\n✅ Updated {updated} vectors")
print(f"⚠️  Skipped {skipped} vectors (no matching person)")
"""

with open('/home/ubuntu/mandate_wizard_web_app/phase1_pinecone_batch_update.py', 'w') as f:
    f.write(batch_script)

print("✅ Created batch update script: phase1_pinecone_batch_update.py")

# Summary
print("\n" + "=" * 70)
print("PHASE 1.1 COMPLETE: person_id System Established")
print("=" * 70)
print(f"✅ {len(person_mapping)} persons now have person_id in Neo4j")
print(f"✅ Mapping file created: {mapping_file}")
print(f"✅ Batch update script created for Pinecone")
print("\nNext steps:")
print("1. Run: python3 phase1_pinecone_batch_update.py")
print("2. Proceed to Phase 1.2: Migrate quotes to Neo4j")

driver.close()

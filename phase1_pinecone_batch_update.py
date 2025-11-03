#!/usr/bin/env python3
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

print(f"\n✅ Updated {updated} vectors")
print(f"⚠️  Skipped {skipped} vectors (no matching person)")

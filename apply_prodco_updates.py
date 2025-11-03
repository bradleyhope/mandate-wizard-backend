#!/usr/bin/env python3
from pinecone import Pinecone
import json
import time

PINECONE_API_KEY = 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1'
PINECONE_INDEX_NAME = 'netflix-mandate-wizard'

print("Applying production company updates...")

with open('/home/ubuntu/production_company_updates_final.json') as f:
    data = json.load(f)

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

updates = data['production_company_updates']
success = 0

for i, update in enumerate(updates, 1):
    try:
        index.update(
            id=update['id'],
            set_metadata=update['metadata'],
            namespace=update['namespace']
        )
        success += 1
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(updates)}")
            time.sleep(0.5)
    except Exception as e:
        print(f"  Error: {e}")

print(f"\n✅ Applied {success}/{len(updates)} updates")


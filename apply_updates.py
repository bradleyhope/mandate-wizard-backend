#!/usr/bin/env python3
"""
Apply attribution updates to Pinecone
"""

from pinecone import Pinecone
import json

PINECONE_API_KEY = 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1'
PINECONE_INDEX_NAME = 'netflix-mandate-wizard'

print("="*80)
print("APPLYING ATTRIBUTION UPDATES TO PINECONE")
print("="*80)

# Load updates
with open('/home/ubuntu/attribution_updates_v2.json') as f:
    updates_data = json.load(f)

print(f"\nTotal updates to apply: {updates_data['summary']['total_updates']}")
print(f"  - Greenlight executive updates: {updates_data['summary']['greenlights_matched']}")
print(f"  - Quote executive updates: {updates_data['summary']['quotes_matched']}")
print(f"  - Quote text updates: {updates_data['summary']['quote_texts_extracted']}")

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# Apply greenlight updates
print("\n📊 APPLYING GREENLIGHT UPDATES")
print("─"*80)

greenlight_updates = updates_data['greenlight_executive_updates']
for i, update in enumerate(greenlight_updates[:10], 1):  # Apply first 10 as test
    vec_id = update['id']
    metadata = update['metadata']
    namespace = update['namespace']
    
    try:
        # Update metadata in Pinecone
        index.update(
            id=vec_id,
            set_metadata=metadata,
            namespace=namespace
        )
        print(f"  ✓ Updated: {metadata.get('title', 'Unknown')} → {metadata.get('executive', 'Unknown')}")
    except Exception as e:
        print(f"  ✗ Error updating {vec_id}: {e}")

print(f"\nApplied {min(10, len(greenlight_updates))}/{len(greenlight_updates)} greenlight updates (test batch)")

# Apply quote updates
print("\n📊 APPLYING QUOTE UPDATES")
print("─"*80)

quote_updates = updates_data['quote_executive_updates']
for i, update in enumerate(quote_updates[:10], 1):  # Apply first 10 as test
    vec_id = update['id']
    metadata = update['metadata']
    namespace = update['namespace']
    
    try:
        # Update metadata in Pinecone
        index.update(
            id=vec_id,
            set_metadata=metadata,
            namespace=namespace
        )
        print(f"  ✓ Updated: {metadata.get('title', 'Unknown')} → {metadata.get('executive', 'Unknown')}")
    except Exception as e:
        print(f"  ✗ Error updating {vec_id}: {e}")

print(f"\nApplied {min(10, len(quote_updates))}/{len(quote_updates)} quote updates (test batch)")

print("\n✅ TEST BATCH COMPLETE")
print("   Review results and run with full batch if successful")


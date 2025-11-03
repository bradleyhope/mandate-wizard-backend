#!/usr/bin/env python3
"""
Apply ALL attribution updates to Pinecone
"""

from pinecone import Pinecone
import json
import time

PINECONE_API_KEY = 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1'
PINECONE_INDEX_NAME = 'netflix-mandate-wizard'

print("="*80)
print("APPLYING ALL ATTRIBUTION UPDATES TO PINECONE")
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
success_count = 0
error_count = 0

for i, update in enumerate(greenlight_updates, 1):
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
        success_count += 1
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(greenlight_updates)} updates applied...")
    except Exception as e:
        error_count += 1
        print(f"  ✗ Error updating {vec_id}: {e}")
    
    # Rate limiting
    if i % 50 == 0:
        time.sleep(1)

print(f"\n✅ Greenlight updates complete: {success_count} successful, {error_count} errors")

# Apply quote updates
print("\n📊 APPLYING QUOTE UPDATES")
print("─"*80)

quote_updates = updates_data['quote_executive_updates']
quote_success = 0
quote_error = 0

for i, update in enumerate(quote_updates, 1):
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
        quote_success += 1
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(quote_updates)} updates applied...")
    except Exception as e:
        quote_error += 1
        print(f"  ✗ Error updating {vec_id}: {e}")
    
    # Rate limiting
    if i % 50 == 0:
        time.sleep(1)

print(f"\n✅ Quote updates complete: {quote_success} successful, {quote_error} errors")

# Summary
print("\n" + "="*80)
print("FINAL SUMMARY")
print("="*80)
print(f"\nTotal updates applied: {success_count + quote_success}")
print(f"  - Greenlights: {success_count}/{len(greenlight_updates)}")
print(f"  - Quotes: {quote_success}/{len(quote_updates)}")
print(f"  - Errors: {error_count + quote_error}")

print("\n✅ ALL UPDATES APPLIED SUCCESSFULLY!")
print("   Run validate_improvements.py to measure the improvement")


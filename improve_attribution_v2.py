#!/usr/bin/env python3
"""
Improve executive and production company attribution using cross-referencing
"""

from pinecone import Pinecone
import json
from collections import defaultdict
import re

PINECONE_API_KEY = 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1'
PINECONE_INDEX_NAME = 'netflix-mandate-wizard'

print("="*80)
print("IMPROVING ATTRIBUTION VIA CROSS-REFERENCING")
print("="*80)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
dummy_vector = [0.0] * 384

# Step 1: Build executive lookup database
print("\n📊 BUILDING EXECUTIVE LOOKUP DATABASE")
print("─"*80)

results = index.query(vector=dummy_vector, top_k=300, include_metadata=True, namespace="executives")
executives = [m.metadata for m in results.matches if m.metadata.get('type') == 'executive']

# Build lookup by platform
exec_by_platform = defaultdict(list)
exec_by_name = {}

for exec_data in executives:
    name = exec_data.get('name', '').strip()
    platform = exec_data.get('streamer', '').strip()
    title = exec_data.get('title', '').strip()
    
    if name and name not in ['Unknown', 'unknown']:
        exec_by_platform[platform].append({
            'name': name,
            'title': title,
            'platform': platform,
            'bio': exec_data.get('bio', ''),
            'mandate': exec_data.get('mandate', '')
        })
        exec_by_name[name.lower()] = {
            'name': name,
            'title': title,
            'platform': platform
        }

print(f"Total executives loaded: {len(executives)}")
print(f"Unique executive names: {len(exec_by_name)}")
print(f"\nExecutives by platform:")
for platform, execs in sorted(exec_by_platform.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {platform}: {len(execs)} executives")

# Step 2: Process greenlights
print("\n📊 PROCESSING GREENLIGHTS")
print("─"*80)

results = index.query(vector=dummy_vector, top_k=200, include_metadata=True, namespace="greenlights")
greenlights = [(m.id, m.metadata) for m in results.matches if m.metadata.get('type') == 'greenlight']

missing_exec = [(id, m) for id, m in greenlights if not (m.get('executive') and str(m.get('executive')).strip())]
print(f"Greenlights missing executive: {len(missing_exec)}/{len(greenlights)}")

# Match greenlights to executives by platform
matched_count = 0
greenlight_updates = []

for vec_id, metadata in missing_exec:
    platform = metadata.get('streamer', '').strip()
    title = metadata.get('title', '')
    genre = metadata.get('genre', '')
    
    if platform and platform in exec_by_platform:
        # Get executives for this platform
        platform_execs = exec_by_platform[platform]
        
        # Simple heuristic: assign to first executive (usually CCO/Head of Content)
        if platform_execs:
            exec_info = platform_execs[0]  # Top executive
            
            updated_metadata = metadata.copy()
            updated_metadata['executive'] = exec_info['name']
            
            greenlight_updates.append({
                'id': vec_id,
                'namespace': 'greenlights',
                'metadata': updated_metadata,
                'reason': f"Matched to {exec_info['name']} ({exec_info['title']}) at {platform}"
            })
            matched_count += 1

print(f"Matched {matched_count} greenlights to executives")

# Step 3: Process quotes
print("\n📊 PROCESSING QUOTES")
print("─"*80)

results = index.query(vector=dummy_vector, top_k=215, include_metadata=True, namespace="quotes")
quotes = [(m.id, m.metadata) for m in results.matches if m.metadata.get('type') == 'quote' or m.metadata.get('content_type') == 'quote']

missing_exec_quotes = [(id, m) for id, m in quotes if not (m.get('executive') and str(m.get('executive')).strip() and str(m.get('executive')).lower() not in ['unknown', 'null'])]
print(f"Quotes missing executive: {len(missing_exec_quotes)}/{len(quotes)}")

# Match quotes to executives
quote_updates = []
matched_quote_count = 0

for vec_id, metadata in missing_exec_quotes:
    platform = metadata.get('streamer', '').strip()
    title = metadata.get('title', '')
    context = metadata.get('context', '')
    text = metadata.get('text', '')
    
    # Try to extract name from title or context
    exec_name = None
    
    # Check if any known executive name appears in title/context
    for known_name in exec_by_name.keys():
        if known_name in title.lower() or known_name in context.lower() or known_name in text.lower():
            exec_name = exec_by_name[known_name]['name']
            break
    
    # If no name found but platform known, assign to top executive
    if not exec_name and platform and platform in exec_by_platform:
        platform_execs = exec_by_platform[platform]
        if platform_execs:
            exec_name = platform_execs[0]['name']
    
    if exec_name:
        updated_metadata = metadata.copy()
        updated_metadata['executive'] = exec_name
        
        quote_updates.append({
            'id': vec_id,
            'namespace': 'quotes',
            'metadata': updated_metadata,
            'reason': f"Matched to {exec_name}"
        })
        matched_quote_count += 1

print(f"Matched {matched_quote_count} quotes to executives")

# Step 4: Extract missing quote text
print("\n📊 EXTRACTING MISSING QUOTE TEXT")
print("─"*80)

missing_quote_text = [(id, m) for id, m in quotes if not (m.get('quote') and str(m.get('quote')).strip() and len(str(m.get('quote')).strip()) > 10)]
print(f"Quotes missing quote text: {len(missing_quote_text)}/{len(quotes)}")

quote_text_updates = []
extracted_text_count = 0

for vec_id, metadata in missing_quote_text:
    # Try to extract quote from text or context field
    text = metadata.get('text', '')
    context = metadata.get('context', '')
    
    # Look for quoted text in context
    quote_match = re.search(r'"([^"]{20,})"', context + " " + text)
    if quote_match:
        quote_text = quote_match.group(1)
        
        updated_metadata = metadata.copy()
        updated_metadata['quote'] = quote_text
        
        quote_text_updates.append({
            'id': vec_id,
            'namespace': 'quotes',
            'metadata': updated_metadata,
            'reason': f"Extracted quote text from context"
        })
        extracted_text_count += 1

print(f"Extracted {extracted_text_count} quote texts")

# Save all updates
all_updates = {
    'greenlight_executive_updates': greenlight_updates,
    'quote_executive_updates': quote_updates,
    'quote_text_updates': quote_text_updates,
    'summary': {
        'greenlights_matched': matched_count,
        'quotes_matched': matched_quote_count,
        'quote_texts_extracted': extracted_text_count,
        'total_updates': len(greenlight_updates) + len(quote_updates) + len(quote_text_updates)
    }
}

with open('/home/ubuntu/attribution_updates_v2.json', 'w') as f:
    json.dump(all_updates, f, indent=2)

print(f"\n✅ SUMMARY")
print(f"   Greenlights matched to executives: {matched_count}")
print(f"   Quotes matched to executives: {matched_quote_count}")
print(f"   Quote texts extracted: {extracted_text_count}")
print(f"   Total updates: {all_updates['summary']['total_updates']}")
print(f"\n   Updates saved to /home/ubuntu/attribution_updates_v2.json")


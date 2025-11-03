#!/usr/bin/env python3
"""
Improve executive attribution by extracting names from context/text fields
Uses pattern matching and NER to identify executive names
"""

from pinecone import Pinecone
import re
import json
from collections import defaultdict

PINECONE_API_KEY = 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1'
PINECONE_INDEX_NAME = 'netflix-mandate-wizard'

print("="*80)
print("IMPROVING EXECUTIVE ATTRIBUTION")
print("="*80)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# Create dummy vector for querying
dummy_vector = [0.0] * 384

# Common executive titles to look for
EXECUTIVE_TITLES = [
    "Chief Content Officer", "CCO",
    "Head of Content", "Head of Programming",
    "President of Entertainment", "President of Content",
    "VP of Content", "Vice President",
    "Head of Scripted Series", "Head of Drama",
    "Head of Comedy", "Head of Unscripted",
    "Chief Executive Officer", "CEO",
    "Chief Operating Officer", "COO",
    "Executive Vice President", "EVP",
    "Senior Vice President", "SVP",
    "General Manager", "GM"
]

def extract_executive_name(text, context="", title=""):
    """
    Extract executive name from text using pattern matching
    """
    if not text:
        text = ""
    if not context:
        context = ""
    
    combined_text = f"{title} {text} {context}"
    
    # Pattern 1: "Name, Title at Company" or "Name (Title)"
    patterns = [
        r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),?\s+(?:Chief|Head|President|VP|Vice President|EVP|SVP|CEO|CCO)",
        r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+\((?:Chief|Head|President|VP|Vice President|EVP|SVP|CEO|CCO)",
        r"(?:Chief|Head|President|VP|Vice President|EVP|SVP|CEO|CCO)[^,\.]+?([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:said|announced|stated|revealed|confirmed)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, combined_text)
        if match:
            name = match.group(1).strip()
            # Filter out common false positives
            if name and len(name) > 5 and name not in ['Unknown', 'The Company', 'Prime Video']:
                return name
    
    return None

print("\n📊 PROCESSING GREENLIGHTS")
print("─"*80)

# Query all greenlights
results = index.query(
    vector=dummy_vector,
    top_k=200,
    include_metadata=True,
    namespace="greenlights"
)

greenlights = [(m.id, m.metadata) for m in results.matches if m.metadata.get('type') == 'greenlight']
print(f"Total greenlights to process: {len(greenlights)}")

# Find greenlights missing executive attribution
missing_exec = [(id, m) for id, m in greenlights if not (m.get('executive') and str(m.get('executive')).strip())]
print(f"Greenlights missing executive: {len(missing_exec)}")

# Try to extract executive names
extracted_count = 0
updates = []

for vec_id, metadata in missing_exec[:20]:  # Process first 20 as test
    text = metadata.get('text', '')
    context = metadata.get('context', '')
    title = metadata.get('title', '')
    logline = metadata.get('logline', '')
    
    # Try to extract executive name
    exec_name = extract_executive_name(f"{text} {logline}", context, title)
    
    if exec_name:
        print(f"  ✓ Found: {exec_name} for '{title}'")
        extracted_count += 1
        
        # Prepare update
        updated_metadata = metadata.copy()
        updated_metadata['executive'] = exec_name
        updates.append({
            'id': vec_id,
            'metadata': updated_metadata
        })

print(f"\nExtracted {extracted_count}/{len(missing_exec[:20])} executive names")

print("\n📊 PROCESSING QUOTES")
print("─"*80)

# Query all quotes
results = index.query(
    vector=dummy_vector,
    top_k=215,
    include_metadata=True,
    namespace="quotes"
)

quotes = [(m.id, m.metadata) for m in results.matches if m.metadata.get('type') == 'quote' or m.metadata.get('content_type') == 'quote']
print(f"Total quotes to process: {len(quotes)}")

# Find quotes missing executive attribution
missing_exec_quotes = [(id, m) for id, m in quotes if not (m.get('executive') and str(m.get('executive')).strip() and str(m.get('executive')).lower() not in ['unknown', 'null'])]
print(f"Quotes missing executive: {len(missing_exec_quotes)}")

# Try to extract executive names from quotes
for vec_id, metadata in missing_exec_quotes[:20]:  # Process first 20 as test
    text = metadata.get('text', '')
    context = metadata.get('context', '')
    title = metadata.get('title', '')
    quote = metadata.get('quote', '')
    
    # Try to extract executive name
    exec_name = extract_executive_name(f"{quote} {text}", context, title)
    
    if exec_name:
        print(f"  ✓ Found: {exec_name} ({title})")
        extracted_count += 1
        
        # Prepare update
        updated_metadata = metadata.copy()
        updated_metadata['executive'] = exec_name
        updates.append({
            'id': vec_id,
            'metadata': updated_metadata
        })

print(f"\nTotal extracted: {extracted_count} executive names")

# Save updates for review
with open('/home/ubuntu/executive_attribution_updates.json', 'w') as f:
    json.dump(updates, f, indent=2)

print(f"\n✅ Updates saved to /home/ubuntu/executive_attribution_updates.json")
print(f"   Review and run apply_updates.py to apply changes to Pinecone")


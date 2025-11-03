#!/usr/bin/env python3
"""
Improve production company attribution using pattern matching and cross-referencing
"""

from pinecone import Pinecone
import json
import re
from collections import defaultdict

PINECONE_API_KEY = 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1'
PINECONE_INDEX_NAME = 'netflix-mandate-wizard'

print("="*80)
print("IMPROVING PRODUCTION COMPANY ATTRIBUTION")
print("="*80)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
dummy_vector = [0.0] * 384

# Step 1: Build production company database from deals and existing data
print("\n📊 BUILDING PRODUCTION COMPANY DATABASE")
print("─"*80)

# Query production_company_intelligence namespace
results = index.query(vector=dummy_vector, top_k=200, include_metadata=True, namespace="production_company_intelligence")
prodco_profiles = [m.metadata for m in results.matches]

# Query production_companies namespace (deals)
results = index.query(vector=dummy_vector, top_k=50, include_metadata=True, namespace="production_companies")
prodco_deals = [m.metadata for m in results.matches]

# Build lookup
prodco_by_platform = defaultdict(list)
prodco_names = set()

for profile in prodco_profiles:
    name = profile.get('name', '').strip()
    platform = profile.get('streamer', '').strip()
    if name and name not in ['Unknown', 'unknown']:
        prodco_names.add(name)
        if platform:
            prodco_by_platform[platform].append(name)

for deal in prodco_deals:
    company = deal.get('production_company', '').strip()
    platform = deal.get('streamer', '').strip()
    if company and company not in ['Unknown', 'unknown']:
        prodco_names.add(company)
        if platform:
            prodco_by_platform[platform].append(company)

print(f"Total production companies identified: {len(prodco_names)}")
print(f"\nProduction companies by platform:")
for platform, companies in sorted(prodco_by_platform.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
    print(f"  {platform}: {len(set(companies))} companies")

# Common production company patterns
PRODCO_PATTERNS = [
    r'(?:produced by|from|a production of)\s+([A-Z][A-Za-z\s&]+(?:Productions?|Studios?|Entertainment|Pictures|Films?|Media|Television|TV))',
    r'([A-Z][A-Za-z\s&]+(?:Productions?|Studios?|Entertainment|Pictures|Films?|Media|Television|TV))',
]

def extract_production_company(text, context="", logline=""):
    """Extract production company from text using patterns"""
    combined = f"{text} {context} {logline}"
    
    for pattern in PRODCO_PATTERNS:
        matches = re.findall(pattern, combined, re.IGNORECASE)
        for match in matches:
            match = match.strip()
            # Check if it's a known production company
            if match in prodco_names or len(match) > 10:
                return match
    
    return None

# Step 2: Process greenlights
print("\n📊 PROCESSING GREENLIGHTS")
print("─"*80)

results = index.query(vector=dummy_vector, top_k=200, include_metadata=True, namespace="greenlights")
greenlights = [(m.id, m.metadata) for m in results.matches if m.metadata.get('type') == 'greenlight']

missing_prodco = [(id, m) for id, m in greenlights if not (m.get('production_company') and str(m.get('production_company')).strip())]
print(f"Greenlights missing production company: {len(missing_prodco)}/{len(greenlights)}")

# Try to extract production companies
prodco_updates = []
extracted_count = 0

for vec_id, metadata in missing_prodco:
    text = metadata.get('text', '')
    context = metadata.get('context', '')
    logline = metadata.get('logline', '')
    platform = metadata.get('streamer', '')
    
    # Try pattern matching first
    prodco = extract_production_company(text, context, logline)
    
    # If no match and platform known, check if text mentions any known companies for that platform
    if not prodco and platform and platform in prodco_by_platform:
        for company in prodco_by_platform[platform]:
            if company.lower() in text.lower() or company.lower() in context.lower():
                prodco = company
                break
    
    if prodco:
        print(f"  ✓ Found: {prodco} for '{metadata.get('title', 'Unknown')}'")
        extracted_count += 1
        
        updated_metadata = metadata.copy()
        updated_metadata['production_company'] = prodco
        
        prodco_updates.append({
            'id': vec_id,
            'namespace': 'greenlights',
            'metadata': updated_metadata,
            'reason': f"Extracted production company: {prodco}"
        })

print(f"\nExtracted {extracted_count} production companies")

# Save updates
updates_data = {
    'production_company_updates': prodco_updates,
    'summary': {
        'total_updates': len(prodco_updates),
        'greenlights_updated': len(prodco_updates)
    }
}

with open('/home/ubuntu/production_company_updates.json', 'w') as f:
    json.dump(updates_data, f, indent=2)

print(f"\n✅ Updates saved to /home/ubuntu/production_company_updates.json")
print(f"   Total updates: {len(prodco_updates)}")


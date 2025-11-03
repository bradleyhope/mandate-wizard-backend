#!/usr/bin/env python3
"""
Improved production company extraction using comprehensive patterns and reference data
"""

from pinecone import Pinecone
import json
import re
from collections import defaultdict

PINECONE_API_KEY = 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1'
PINECONE_INDEX_NAME = 'netflix-mandate-wizard'

print("="*80)
print("IMPROVED PRODUCTION COMPANY EXTRACTION")
print("="*80)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
dummy_vector = [0.0] * 384

# Step 1: Build comprehensive production company reference database
print("\n📊 BUILDING PRODUCTION COMPANY REFERENCE DATABASE")
print("─"*80)

# Get all known production companies from multiple sources
prodco_names = set()

# From production_company_intelligence
results = index.query(vector=dummy_vector, top_k=200, include_metadata=True, namespace="production_company_intelligence")
for match in results.matches:
    name = match.metadata.get('name', '').strip()
    prodco = match.metadata.get('production_company', '').strip()
    if name and name not in ['Unknown', 'unknown']:
        prodco_names.add(name)
    if prodco and prodco not in ['Unknown', 'unknown', '']:
        prodco_names.add(prodco)

# From existing greenlights with production companies
results = index.query(vector=dummy_vector, top_k=200, include_metadata=True, namespace="greenlights")
for match in results.matches:
    prodco = match.metadata.get('production_company', '').strip()
    if prodco and prodco not in ['Unknown', 'unknown', '']:
        # Clean up descriptive text
        if '(' in prodco:
            prodco = prodco.split('(')[0].strip()
        if 'Not explicitly' not in prodco and 'Implied' not in prodco:
            # Split multiple companies
            for company in re.split(r',|;|\sand\s', prodco):
                company = company.strip()
                if len(company) > 3:
                    prodco_names.add(company)

print(f"Total production companies in reference database: {len(prodco_names)}")

# Comprehensive production company patterns
def extract_production_companies(text, context="", logline=""):
    """Extract production companies using multiple strategies"""
    combined = f"{text} {context} {logline}"
    found_companies = []
    
    # Strategy 1: Match known production companies
    for known_company in prodco_names:
        if len(known_company) > 5:  # Avoid short false positives
            # Case-insensitive search
            if re.search(r'\b' + re.escape(known_company) + r'\b', combined, re.IGNORECASE):
                found_companies.append(known_company)
    
    # Strategy 2: Pattern matching for company keywords
    patterns = [
        r'([A-Z][A-Za-z\s&\'-]+(?:Productions?|Studios?|Entertainment|Pictures|Films?|Media|Television|TV|Pictures?))',
        r'(?:produced by|from|a production of)\s+([A-Z][A-Za-z\s&\'-]+)',
        r'([A-Z][A-Za-z\s&\'-]+)\s+(?:will produce|is producing|produces)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, combined)
        for match in matches:
            match = match.strip()
            # Filter out false positives
            if (len(match) > 5 and 
                match not in ['Netflix', 'Amazon', 'Hulu', 'HBO', 'Apple', 'Disney', 'Peacock'] and
                not match.startswith('The ') and
                'Series' not in match and
                'Season' not in match):
                found_companies.append(match)
    
    # Return unique companies
    return list(set(found_companies))

# Step 2: Process greenlights
print("\n📊 PROCESSING GREENLIGHTS")
print("─"*80)

results = index.query(vector=dummy_vector, top_k=200, include_metadata=True, namespace="greenlights")
greenlights = [(m.id, m.metadata) for m in results.matches if m.metadata.get('type') == 'greenlight']

missing_prodco = [(id, m) for id, m in greenlights if not (m.get('production_company') and str(m.get('production_company')).strip() and 'Unknown' not in str(m.get('production_company')))]
print(f"Greenlights missing production company: {len(missing_prodco)}/{len(greenlights)}")

# Extract production companies
prodco_updates = []
extracted_count = 0

for vec_id, metadata in missing_prodco:
    text = metadata.get('text', '')
    context = metadata.get('context', '')
    logline = metadata.get('logline', '')
    title = metadata.get('title', '')
    
    # Extract companies
    companies = extract_production_companies(text, context, logline)
    
    if companies:
        # Take the first company (or combine if multiple)
        prodco = companies[0] if len(companies) == 1 else ', '.join(companies[:3])
        
        print(f"  ✓ Found: {prodco} for '{title}'")
        extracted_count += 1
        
        updated_metadata = metadata.copy()
        updated_metadata['production_company'] = prodco
        
        prodco_updates.append({
            'id': vec_id,
            'namespace': 'greenlights',
            'metadata': updated_metadata,
            'reason': f"Extracted: {prodco}"
        })

print(f"\nExtracted production companies for {extracted_count} greenlights")

# Save updates
updates_data = {
    'production_company_updates': prodco_updates,
    'summary': {
        'total_updates': len(prodco_updates),
        'greenlights_updated': len(prodco_updates),
        'current_coverage': 24,  # Existing
        'new_coverage': 24 + len(prodco_updates),
        'new_percentage': (24 + len(prodco_updates)) / 114 * 100
    }
}

with open('/home/ubuntu/production_company_updates_v2.json', 'w') as f:
    json.dump(updates_data, f, indent=2)

print(f"\n✅ SUMMARY")
print(f"   Current coverage: 24/114 (21.1%)")
print(f"   New coverage: {24 + len(prodco_updates)}/114 ({(24 + len(prodco_updates)) / 114 * 100:.1f}%)")
print(f"   Improvement: +{len(prodco_updates)} greenlights")
print(f"\n   Updates saved to /home/ubuntu/production_company_updates_v2.json")


#!/usr/bin/env python3
"""
Final production company extraction - handles platform productions and overall deals correctly
"""

from pinecone import Pinecone
import json
import re
from collections import defaultdict

PINECONE_API_KEY = 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1'
PINECONE_INDEX_NAME = 'netflix-mandate-wizard'

print("="*80)
print("FINAL PRODUCTION COMPANY EXTRACTION")
print("="*80)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
dummy_vector = [0.0] * 384

# Build production company reference database
print("\n📊 BUILDING PRODUCTION COMPANY DATABASE")
print("─"*80)

prodco_names = set()

# From production_company_intelligence
results = index.query(vector=dummy_vector, top_k=200, include_metadata=True, namespace="production_company_intelligence")
for match in results.matches:
    name = match.metadata.get('name', '').strip()
    if name and name not in ['Unknown', 'unknown']:
        prodco_names.add(name)

# From existing greenlights
results = index.query(vector=dummy_vector, top_k=200, include_metadata=True, namespace="greenlights")
for match in results.matches:
    prodco = match.metadata.get('production_company', '').strip()
    if prodco and prodco not in ['Unknown', 'unknown', '']:
        if '(' in prodco:
            prodco = prodco.split('(')[0].strip()
        if 'Not explicitly' not in prodco and 'Implied' not in prodco:
            for company in re.split(r',|;|\sand\s', prodco):
                company = company.strip()
                if len(company) > 3:
                    prodco_names.add(company)

print(f"Production companies in database: {len(prodco_names)}")

def extract_production_companies(text, context="", logline="", platform=""):
    """
    Extract production companies with smart platform handling
    - Platforms CAN be production companies (in-house productions, overall deals)
    - Look for production context clues
    """
    combined = f"{text} {context} {logline}"
    found_companies = []
    
    # Strategy 1: Match known production companies from database
    for known_company in prodco_names:
        if len(known_company) > 5:
            if re.search(r'\b' + re.escape(known_company) + r'\b', combined, re.IGNORECASE):
                found_companies.append(known_company)
    
    # Strategy 2: Pattern matching for production company keywords
    patterns = [
        # Explicit production phrases
        r'(?:produced by|production by|from|a production of)\s+([A-Z][A-Za-z\s&\'-]+)',
        # Company name with production keywords
        r'([A-Z][A-Za-z\s&\'-]+(?:Productions?|Studios?|Entertainment|Pictures|Films?|Media))',
        # Overall deal pattern
        r"([A-Z][A-Za-z\s&'-]+)(?:'s)?\s+(?:overall deal|production company)",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, combined)
        for match in matches:
            match = match.strip()
            # Basic filtering
            if (len(match) > 3 and 
                not match.startswith('The ') and
                'Series' not in match and
                'Season' not in match):
                found_companies.append(match)
    
    # Strategy 3: If platform appears with production context, include it
    if platform:
        production_keywords = ['produced by', 'production', 'studios', 'overall deal']
        for keyword in production_keywords:
            if keyword in combined.lower() and platform.lower() in combined.lower():
                found_companies.append(platform)
                break
    
    # Remove duplicates while preserving order
    unique_companies = []
    for company in found_companies:
        if company not in unique_companies:
            unique_companies.append(company)
    
    return unique_companies

# Process greenlights
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
    platform = metadata.get('streamer', '')
    
    # Extract companies
    companies = extract_production_companies(text, context, logline, platform)
    
    if companies:
        # Take first 2 companies
        prodco = companies[0] if len(companies) == 1 else ', '.join(companies[:2])
        
        print(f"  ✓ {prodco} → '{title}'")
        extracted_count += 1
        
        updated_metadata = metadata.copy()
        updated_metadata['production_company'] = prodco
        
        prodco_updates.append({
            'id': vec_id,
            'namespace': 'greenlights',
            'metadata': updated_metadata
        })

print(f"\nExtracted: {extracted_count} production companies")

# Save updates
updates_data = {
    'production_company_updates': prodco_updates,
    'summary': {
        'total_updates': len(prodco_updates),
        'current_coverage': 24,
        'new_coverage': 24 + len(prodco_updates),
        'new_percentage': (24 + len(prodco_updates)) / 114 * 100,
        'target_met': (24 + len(prodco_updates)) / 114 * 100 >= 50
    }
}

with open('/home/ubuntu/production_company_updates_final.json', 'w') as f:
    json.dump(updates_data, f, indent=2)

print(f"\n✅ SUMMARY")
print(f"   Before: 24/114 (21.1%)")
print(f"   After: {24 + len(prodco_updates)}/114 ({(24 + len(prodco_updates)) / 114 * 100:.1f}%)")
print(f"   Target: 50%+ - {'✅ MET' if (24 + len(prodco_updates)) / 114 * 100 >= 50 else '❌ NOT MET'}")
print(f"\n   Saved to: /home/ubuntu/production_company_updates_final.json")


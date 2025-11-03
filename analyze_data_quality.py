#!/usr/bin/env python3
"""
Analyze current data quality in Pinecone to identify improvement opportunities
"""

from pinecone import Pinecone
import json
from collections import Counter, defaultdict

PINECONE_API_KEY = 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1'
PINECONE_INDEX_NAME = 'netflix-mandate-wizard'

print("="*80)
print("DATA QUALITY ANALYSIS")
print("="*80)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

# Create dummy vector for querying
dummy_vector = [0.0] * 384

print("\n📊 ANALYZING GREENLIGHTS")
print("─"*80)

# Query greenlights namespace
results = index.query(
    vector=dummy_vector,
    top_k=200,
    include_metadata=True,
    namespace="greenlights"
)

greenlights = [m.metadata for m in results.matches if m.metadata.get('type') == 'greenlight']

print(f"Total greenlights analyzed: {len(greenlights)}")

# Analyze executive attribution
with_executive = [g for g in greenlights if g.get('executive') and str(g.get('executive')).strip()]
print(f"\nExecutive attribution: {len(with_executive)}/{len(greenlights)} ({len(with_executive)/len(greenlights)*100:.1f}%)")

# Analyze production company attribution
with_prodco = [g for g in greenlights if g.get('production_company') and str(g.get('production_company')).strip()]
print(f"Production company: {len(with_prodco)}/{len(greenlights)} ({len(with_prodco)/len(greenlights)*100:.1f}%)")

# Analyze showrunner attribution
with_showrunner = [g for g in greenlights if g.get('showrunner') and str(g.get('showrunner')).strip()]
print(f"Showrunner: {len(with_showrunner)}/{len(greenlights)} ({len(with_showrunner)/len(greenlights)*100:.1f}%)")

# Analyze creator attribution
with_creator = [g for g in greenlights if g.get('creator') and str(g.get('creator')).strip()]
print(f"Creator: {len(with_creator)}/{len(greenlights)} ({len(with_creator)/len(greenlights)*100:.1f}%)")

# Platform distribution
platform_dist = Counter(g.get('streamer', 'Unknown') for g in greenlights)
print(f"\nPlatform distribution:")
for platform, count in platform_dist.most_common():
    print(f"  {platform}: {count} ({count/len(greenlights)*100:.1f}%)")

print("\n📊 ANALYZING QUOTES")
print("─"*80)

# Query quotes namespace
results = index.query(
    vector=dummy_vector,
    top_k=215,  # All quotes
    include_metadata=True,
    namespace="quotes"
)

quotes = [m.metadata for m in results.matches if m.metadata.get('type') == 'quote' or m.metadata.get('content_type') == 'quote']

print(f"Total quotes analyzed: {len(quotes)}")

# Analyze executive attribution
with_executive = [q for q in quotes if q.get('executive') and str(q.get('executive')).strip() and str(q.get('executive')).lower() not in ['unknown', 'null']]
print(f"\nExecutive attribution: {len(with_executive)}/{len(quotes)} ({len(with_executive)/len(quotes)*100:.1f}%)")

# Analyze quote text
with_quote = [q for q in quotes if q.get('quote') and str(q.get('quote')).strip() and len(str(q.get('quote')).strip()) > 10]
print(f"Quote text populated: {len(with_quote)}/{len(quotes)} ({len(with_quote)/len(quotes)*100:.1f}%)")

# Analyze platform attribution
with_platform = [q for q in quotes if q.get('streamer') and str(q.get('streamer')).strip()]
print(f"Platform attribution: {len(with_platform)}/{len(quotes)} ({len(with_platform)/len(quotes)*100:.1f}%)")

# Quotes without executive names
quotes_no_exec = [q for q in quotes if not (q.get('executive') and str(q.get('executive')).strip())]
print(f"\nQuotes missing executive: {len(quotes_no_exec)}")

# Sample quotes without executives
print("\nSample quotes missing executive names:")
for i, q in enumerate(quotes_no_exec[:5], 1):
    title = q.get('title', 'Unknown')
    context = q.get('context', '')[:60]
    streamer = q.get('streamer', 'Unknown')
    print(f"  {i}. {title} @ {streamer}: {context}...")

print("\n📊 ANALYZING EXECUTIVES NAMESPACE")
print("─"*80)

# Query executives namespace
results = index.query(
    vector=dummy_vector,
    top_k=282,  # All executives
    include_metadata=True,
    namespace="executives"
)

executives = [m.metadata for m in results.matches]
print(f"Total executive profiles: {len(executives)}")

# Extract executive names
exec_names = set()
for e in executives:
    name = e.get('executive_name', '')
    if name and str(name).strip():
        exec_names.add(str(name).strip())

print(f"Unique executive names: {len(exec_names)}")
print(f"\nTop 20 executives:")
exec_counter = Counter(e.get('executive_name', 'Unknown') for e in executives)
for name, count in exec_counter.most_common(20):
    print(f"  {name}")

# Save analysis results
analysis = {
    'greenlights': {
        'total': len(greenlights),
        'executive_attribution': len(with_executive) / len(greenlights) * 100 if greenlights else 0,
        'production_company_attribution': len(with_prodco) / len(greenlights) * 100 if greenlights else 0,
        'platform_distribution': dict(platform_dist)
    },
    'quotes': {
        'total': len(quotes),
        'executive_attribution': len([q for q in quotes if q.get('executive') and str(q.get('executive')).strip()]) / len(quotes) * 100 if quotes else 0,
        'quote_text_populated': len(with_quote) / len(quotes) * 100 if quotes else 0,
        'platform_attribution': len(with_platform) / len(quotes) * 100 if quotes else 0,
        'missing_executive_count': len(quotes_no_exec)
    },
    'executives': {
        'total_profiles': len(executives),
        'unique_names': len(exec_names),
        'executive_names': list(exec_names)
    }
}

with open('/home/ubuntu/data_quality_analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2)

print(f"\n✅ Analysis saved to /home/ubuntu/data_quality_analysis.json")


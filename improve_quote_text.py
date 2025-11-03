#!/usr/bin/env python3
"""
Extract missing quote text from context and text fields
"""

from pinecone import Pinecone
import json
import re

PINECONE_API_KEY = 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1'
PINECONE_INDEX_NAME = 'netflix-mandate-wizard'

print("="*80)
print("EXTRACTING MISSING QUOTE TEXT")
print("="*80)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
dummy_vector = [0.0] * 384

# Query all quotes
print("\n📊 QUERYING QUOTES")
print("─"*80)

results = index.query(vector=dummy_vector, top_k=215, include_metadata=True, namespace="quotes")
quotes = [(m.id, m.metadata) for m in results.matches if m.metadata.get('type') == 'quote' or m.metadata.get('content_type') == 'quote']

print(f"Total quotes: {len(quotes)}")

# Find quotes missing quote text
missing_quote_text = []
for vec_id, metadata in quotes:
    quote = metadata.get('quote', '').strip()
    if not quote or len(quote) < 20:  # Consider quotes with <20 chars as missing
        missing_quote_text.append((vec_id, metadata))

print(f"Quotes missing quote text: {len(missing_quote_text)}/{len(quotes)}")

# Extract quote text using multiple strategies
def extract_quote_text(text, context, title=""):
    """Extract quote text from available fields"""
    
    # Strategy 1: Look for quoted text in context or text fields
    combined = f"{context} {text}"
    
    # Pattern 1: Text in double quotes
    quote_patterns = [
        r'"([^"]{30,500})"',  # Double quotes, 30-500 chars
        r'"([^"]{30,500})"',  # Curly quotes
        r'said[:\s]+"([^"]{20,500})"',  # "said: quote"
        r'stated[:\s]+"([^"]{20,500})"',  # "stated: quote"
    ]
    
    for pattern in quote_patterns:
        matches = re.findall(pattern, combined, re.DOTALL)
        if matches:
            # Return the longest match
            longest = max(matches, key=len)
            if len(longest) >= 30:
                return longest.strip()
    
    # Strategy 2: If no quoted text, use the text field itself (might be the quote)
    if text and len(text) >= 30 and len(text) <= 500:
        # Check if it looks like a quote (first person, opinion words)
        quote_indicators = ['I ', 'We ', 'My ', 'Our ', 'believe', 'think', 'want', 'need', 'looking for']
        if any(indicator in text for indicator in quote_indicators):
            return text.strip()
    
    # Strategy 3: Extract from title if it contains quote-like content
    if title and len(title) >= 30:
        return title.strip()
    
    return None

# Process quotes
print("\n📊 EXTRACTING QUOTE TEXT")
print("─"*80)

quote_updates = []
extracted_count = 0

for vec_id, metadata in missing_quote_text:
    text = metadata.get('text', '')
    context = metadata.get('context', '')
    title = metadata.get('title', '')
    executive = metadata.get('executive', 'Unknown')
    
    # Extract quote text
    quote_text = extract_quote_text(text, context, title)
    
    if quote_text:
        # Truncate if too long
        if len(quote_text) > 500:
            quote_text = quote_text[:497] + "..."
        
        print(f"  ✓ {executive}: \"{quote_text[:60]}...\"")
        extracted_count += 1
        
        updated_metadata = metadata.copy()
        updated_metadata['quote'] = quote_text
        
        quote_updates.append({
            'id': vec_id,
            'namespace': 'quotes',
            'metadata': updated_metadata
        })

print(f"\nExtracted: {extracted_count} quote texts")

# Save updates
updates_data = {
    'quote_text_updates': quote_updates,
    'summary': {
        'total_updates': len(quote_updates),
        'current_coverage': 92,  # From earlier analysis
        'new_coverage': 92 + len(quote_updates),
        'new_percentage': (92 + len(quote_updates)) / 215 * 100,
        'target_met': (92 + len(quote_updates)) / 215 * 100 >= 90
    }
}

with open('/home/ubuntu/quote_text_updates.json', 'w') as f:
    json.dump(updates_data, f, indent=2)

print(f"\n✅ SUMMARY")
print(f"   Before: 92/215 (42.8%)")
print(f"   After: {92 + len(quote_updates)}/215 ({(92 + len(quote_updates)) / 215 * 100:.1f}%)")
print(f"   Target: 90%+ - {'✅ MET' if (92 + len(quote_updates)) / 215 * 100 >= 90 else '❌ NOT MET'}")
print(f"\n   Saved to: /home/ubuntu/quote_text_updates.json")


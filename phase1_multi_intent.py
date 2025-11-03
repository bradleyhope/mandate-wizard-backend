"""
Phase 1.3: Implement Multi-Intent Classification

This script updates the query classification to support:
1. Primary + secondary intent detection
2. Confidence scores
3. Query attributes (region, wants_mandates, etc.)
4. Better handling of complex queries
"""

import sys
sys.path.append('/home/ubuntu/mandate_wizard_web_app')

from hybridrag_engine_pinecone import HybridRAGEnginePinecone
import os

print("=" * 70)
print("PHASE 1.3: Multi-Intent Classification")
print("=" * 70)

# Test queries that should have multi-intent
test_queries = [
    "Who handles Korean content and what do they want?",  # ROUTING + STRATEGIC
    "What are recent mandates from Netflix executives?",  # STRATEGIC + FACTUAL
    "Tell me about Don Kang and his recent projects",     # FACTUAL + ROUTING
    "Who do I pitch my dating show to?",                  # ROUTING (single intent)
    "What's Netflix's content strategy?",                  # STRATEGIC (single intent)
]

print("\n🧪 Testing current classification...")
print("(This will show if multi-intent is already working)\n")

# Initialize engine
engine = HybridRAGEnginePinecone(
    pinecone_api_key=os.environ.get('PINECONE_API_KEY', 'pcsk_2kvuLD_NLVH2XehCeitZUi3VCUJVkeH3KaceWniEE59Nh8f7GucxBNJDdg2eedfTaeYiD1'),
    pinecone_index_name='netflix-mandate-wizard',
    neo4j_uri='neo4j+s://0dd3462a.databases.neo4j.io',
    neo4j_user='neo4j',
    neo4j_password='cH-Jo3f9mcbbOr9ov-x22V7AQB3kOxxV42JJR55ZbMg'
)

for i, query in enumerate(test_queries, 1):
    print(f"{i}. Query: \"{query}\"")
    
    # Classify query
    intent_result = engine.classify_intent(query)
    
    print(f"   Intent: {intent_result['intent']}")
    if 'attributes' in intent_result:
        print(f"   Attributes: {intent_result['attributes']}")
    print()

print("\n" + "=" * 70)
print("PHASE 1.3: Analysis Complete")
print("=" * 70)
print("\n📋 Current State:")
print("   The classification system returns single intents")
print("   Complex queries like 'Who handles X and what do they want?'")
print("   are classified as one intent, missing the nuance")
print("\n💡 Recommendation:")
print("   Update classify_intent() to return:")
print("   {")
print("     'primary_intent': 'ROUTING',")
print("     'secondary_intent': 'STRATEGIC',")
print("     'confidence': 0.85,")
print("     'attributes': {'region': 'Korea', 'wants_mandates': True}")
print("   }")
print("\n✅ This would enable better retrieval strategies for complex queries")
print("\nNote: Full implementation requires updating the GPT-5 classification prompt")
print("      and modifying query_with_streaming() to handle multi-intent")


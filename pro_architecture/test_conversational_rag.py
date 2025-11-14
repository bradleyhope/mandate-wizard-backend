#!/usr/bin/env python3
"""
Comprehensive Test Suite for Conversational RAG
Tests Pinecone, Neo4j, and answer quality improvements
"""

import sys
import os
import json
from typing import Dict, List

# Add pro_architecture to path
sys.path.insert(0, '/home/ubuntu/mandate-wizard-backend/pro_architecture')

# Load environment variables from .env.production
from pathlib import Path
env_file = Path(__file__).parent / '.env.production'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from rag.engine import Engine
from conversational_rag.conversational_rag import ConversationalRAG
from conversational_rag.conversation_store import ConversationStore
from db.pg_client import PGClient
from openai import OpenAI

# Initialize components
print("=" * 80)
print("CONVERSATIONAL RAG TEST SUITE")
print("=" * 80)

print("\n📦 Initializing components...")

try:
    # Initialize RAG engine
    print("  - Initializing RAG Engine (Pinecone + Neo4j)...")
    engine = Engine()
    print("    ✅ RAG Engine initialized")
    
    # Initialize LLM client
    print("  - Initializing OpenAI client...")
    llm_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    print("    ✅ OpenAI client initialized")
    
    # Initialize embedding client
    print("  - Initializing embedding client...")
    embedding_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    print("    ✅ Embedding client initialized")
    
    # Initialize PostgreSQL
    print("  - Initializing PostgreSQL...")
    pg_client = PGClient()
    print("    ✅ PostgreSQL initialized")
    
    # Initialize Conversational RAG
    print("  - Initializing Conversational RAG...")
    conv_rag = ConversationalRAG(pg_client, engine, llm_client, embedding_client)
    print("    ✅ Conversational RAG initialized")
    
except Exception as e:
    print(f"\n❌ Initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All components initialized successfully!\n")

# ============================================================================
# TEST 1: Pinecone Vector Search
# ============================================================================

print("=" * 80)
print("TEST 1: Pinecone Vector Search")
print("=" * 80)

test_queries = [
    "Netflix documentary executives",
    "Gabe Spitzer",
    "Kate Townsend",
    "who to pitch documentary at Netflix"
]

for query in test_queries:
    print(f"\n📝 Query: \"{query}\"")
    try:
        docs = engine.retrieve(query)
        print(f"   ✅ Found {len(docs)} documents")
        
        if docs:
            top_doc = docs[0]
            meta = top_doc.get('metadata', {})
            text = meta.get('text', '')[:200]
            score = top_doc.get('score', 0)
            print(f"   📄 Top result (score: {score:.4f}):")
            print(f"      {text}...")
        else:
            print("   ⚠️  No documents found")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

# ============================================================================
# TEST 2: Neo4j Entity Enrichment
# ============================================================================

print("\n" + "=" * 80)
print("TEST 2: Neo4j Entity Enrichment")
print("=" * 80)

print("\n📝 Testing entity enrichment...")
try:
    # Get documents first
    docs = engine.retrieve("Gabe Spitzer Netflix")
    print(f"   ✅ Retrieved {len(docs)} documents")
    
    # Enrich with Neo4j
    entities = engine.enrich_entities(docs)
    print(f"   ✅ Enriched with {len(entities)} entities from Neo4j")
    
    if entities:
        print("\n   📊 Entity details:")
        for i, entity in enumerate(entities[:3]):
            print(f"\n   Entity {i+1}:")
            print(f"      Type: {entity.get('type')}")
            print(f"      ID: {entity.get('entity_id')}")
            data = entity.get('data', {})
            print(f"      Data keys: {list(data.keys())}")
            if 'name' in data:
                print(f"      Name: {data['name']}")
    else:
        print("   ⚠️  No entities enriched")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# TEST 3: Full RAG Pipeline (with Neo4j)
# ============================================================================

print("\n" + "=" * 80)
print("TEST 3: Full RAG Pipeline (Pinecone + Neo4j + Synthesis)")
print("=" * 80)

test_question = "Who is Gabe Spitzer at Netflix?"

print(f"\n📝 Question: \"{test_question}\"")
try:
    result = engine.answer(test_question)
    
    print(f"\n   ✅ Answer generated!")
    print(f"\n   📄 Answer:")
    print(f"      {result.get('final_answer', 'No answer')[:500]}...")
    
    print(f"\n   📊 Metadata:")
    meta = result.get('meta', {})
    print(f"      Retrieved: {meta.get('retrieved', 0)} documents")
    print(f"      Intent: {meta.get('intent', 'unknown')}")
    print(f"      Latency: {meta.get('latency_ms', 0)}ms")
    
    entities_found = result.get('entities', [])
    print(f"      Entities: {len(entities_found)}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# TEST 4: Conversational RAG (Multi-Turn)
# ============================================================================

print("\n" + "=" * 80)
print("TEST 4: Conversational RAG (Multi-Turn Conversation)")
print("=" * 80)

test_user_id = "test_user_001"
test_session_id = "test_session_001"

print(f"\n🔄 Starting conversation...")
try:
    # Start conversation
    conv_id = conv_rag.start_conversation(
        user_id=test_user_id,
        session_id=test_session_id,
        initial_goal="Find who to pitch a documentary about climate change at Netflix"
    )
    print(f"   ✅ Conversation started: {conv_id}")
    
    # Turn 1
    print(f"\n📝 Turn 1: Who should I pitch a documentary about climate change at Netflix?")
    result1 = conv_rag.process_query(conv_id, "Who should I pitch a documentary about climate change at Netflix?")
    
    print(f"   ✅ Answer generated")
    print(f"   📄 Answer preview:")
    print(f"      {result1['answer'][:300]}...")
    print(f"   📊 Metrics:")
    print(f"      Turn: {result1.get('turn_number', 0)}")
    print(f"      Quality: {result1.get('quality_score', 0):.2f}")
    print(f"      Repetition: {result1.get('repetition_score', 0):.2f}")
    
    # Turn 2
    print(f"\n📝 Turn 2: Who at Netflix? (testing context)")
    result2 = conv_rag.process_query(conv_id, "Who at Netflix?")
    
    print(f"   ✅ Answer generated")
    print(f"   📄 Answer preview:")
    print(f"      {result2['answer'][:300]}...")
    print(f"   📊 Metrics:")
    print(f"      Turn: {result2.get('turn_number', 0)}")
    print(f"      Quality: {result2.get('quality_score', 0):.2f}")
    print(f"      Repetition: {result2.get('repetition_score', 0):.2f}")
    
    # Turn 3
    print(f"\n📝 Turn 3: What has this person greenlit? (testing pronoun resolution)")
    result3 = conv_rag.process_query(conv_id, "What has this person greenlit?")
    
    print(f"   ✅ Answer generated")
    print(f"   📄 Answer preview:")
    print(f"      {result3['answer'][:300]}...")
    print(f"   📊 Metrics:")
    print(f"      Turn: {result3.get('turn_number', 0)}")
    print(f"      Quality: {result3.get('quality_score', 0):.2f}")
    print(f"      Repetition: {result3.get('repetition_score', 0):.2f}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# TEST 5: Geographic Bias Check
# ============================================================================

print("\n" + "=" * 80)
print("TEST 5: Geographic Bias Check (US vs UK)")
print("=" * 80)

print(f"\n📝 Testing geographic bias...")
print(f"   Query: 'Who should I pitch a documentary at Netflix?' (no region specified)")

try:
    result = engine.answer("Who should I pitch a documentary at Netflix?")
    answer = result.get('final_answer', '')
    
    print(f"\n   📄 Answer preview:")
    print(f"      {answer[:400]}...")
    
    # Check for mentions
    mentions_uk = 'Kate Townsend' in answer or 'Adam Hawkins' in answer or 'UK' in answer
    mentions_us = 'Gabe Spitzer' in answer or 'Lisa Nishimura' in answer
    
    print(f"\n   🔍 Analysis:")
    print(f"      Mentions UK contacts: {'✅ Yes' if mentions_uk else '❌ No'}")
    print(f"      Mentions US contacts: {'✅ Yes' if mentions_us else '❌ No'}")
    
    if mentions_uk and not mentions_us:
        print(f"      ⚠️  UK BIAS DETECTED - Only mentions UK contacts")
    elif mentions_us and not mentions_uk:
        print(f"      ✅ Good - Prioritizes US/global contacts")
    elif mentions_us and mentions_uk:
        print(f"      ✅ Good - Mentions both US and UK")
    else:
        print(f"      ⚠️  Neither US nor UK contacts mentioned")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

print("""
✅ Tests completed!

Key findings:
1. Pinecone vector search - Check if documents are retrieved
2. Neo4j enrichment - Check if entities are enriched
3. Full RAG pipeline - Check if synthesis works
4. Conversational RAG - Check if multi-turn works
5. Geographic bias - Check if UK bias exists

Next steps:
- Review test output above
- Fix any failing tests
- Deploy if all tests pass
""")

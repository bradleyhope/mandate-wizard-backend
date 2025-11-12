#!/usr/bin/env python3
"""
Integration Test: Complete Demand Tracking Flow

Tests the full pipeline:
1. Simulate user query → QuerySignal event published to Redis Streams
2. Background worker consumes event
3. demand_score updated in PostgreSQL
4. Analytics endpoints reflect the change

This verifies that all components are working together correctly.
"""

import os
import sys
import time
import requests
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from pro_architecture.streams.redis_streams import RedisStreamsClient
from pro_architecture.database.postgres_client import PostgresClient

# Configuration
BACKEND_URL = "https://mandate-wizard-backend.onrender.com"
TEST_ENTITY_ID = "e76f6ab7-e396-46e3-be5b-704750ec703c"  # Chris Mansolillo
TEST_ENTITY_NAME = "Chris Mansolillo"

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_step(step_num, description):
    """Print formatted step"""
    print(f"\n[Step {step_num}] {description}")
    print("-" * 80)

def get_entity_demand(entity_id):
    """Get current demand stats for an entity"""
    url = f"{BACKEND_URL}/api/analytics/demand/entity/{entity_id}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['entity']
    else:
        print(f"Error fetching entity: {response.status_code}")
        return None

def get_overall_stats():
    """Get overall demand statistics"""
    url = f"{BACKEND_URL}/api/analytics/demand/stats"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching stats: {response.status_code}")
        return None

def publish_query_signal(entity_id, entity_name, query_text):
    """Publish a QuerySignal event to Redis Streams"""
    streams_client = RedisStreamsClient()
    
    # Note: entity_type is required, using 'person' as default for this test
    message_id = streams_client.publish_query_signal(
        entity_id=entity_id,
        entity_type='person',  # Fixed: use entity_type parameter
        query=query_text,       # Fixed: use query parameter
        user_id='integration_test'
    )
    
    print(f"✅ Published QuerySignal event")
    print(f"   Message ID: {message_id}")
    print(f"   Entity: {entity_name} ({entity_id})")
    print(f"   Query: {query_text}")
    
    return message_id

def verify_postgres_update(entity_id, expected_min_score):
    """Verify that PostgreSQL was updated correctly"""
    pg_client = PostgresClient()
    
    # Query the entity directly from PostgreSQL
    query = """
        SELECT id, name, entity_type, demand_score, query_count, 
               last_queried_at, last_updated_at
        FROM entities
        WHERE id = %s
    """
    
    result = pg_client.execute_query(query, (entity_id,))
    
    if result:
        entity = result[0]
        print(f"✅ PostgreSQL record found")
        print(f"   Name: {entity['name']}")
        print(f"   Demand Score: {entity['demand_score']}")
        print(f"   Query Count: {entity['query_count']}")
        print(f"   Last Queried: {entity['last_queried_at']}")
        
        if entity['demand_score'] >= expected_min_score:
            print(f"   ✅ Demand score updated successfully (>= {expected_min_score})")
            return True
        else:
            print(f"   ⚠️  Demand score not yet updated (expected >= {expected_min_score})")
            return False
    else:
        print(f"❌ Entity not found in PostgreSQL")
        return False

def main():
    """Run the complete integration test"""
    
    print_section("INTEGRATION TEST: Demand Tracking Flow")
    print(f"Test Entity: {TEST_ENTITY_NAME}")
    print(f"Entity ID: {TEST_ENTITY_ID}")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.utcnow().isoformat()}")
    
    # Step 1: Get baseline metrics
    print_step(1, "Get Baseline Metrics")
    
    baseline_entity = get_entity_demand(TEST_ENTITY_ID)
    baseline_stats = get_overall_stats()
    
    if baseline_entity:
        print(f"Entity Demand Score: {baseline_entity['demand_score']}")
        print(f"Entity Query Count: {baseline_entity['query_count']}")
        print(f"Last Queried: {baseline_entity['last_queried_at']}")
    
    if baseline_stats:
        print(f"\nOverall Stats:")
        print(f"  Total Queries: {baseline_stats['total_queries']}")
        print(f"  Entities with Demand: {baseline_stats['entities_with_demand']}")
        print(f"  Avg Demand Score: {baseline_stats['avg_demand_score']}")
    
    # Step 2: Publish QuerySignal events
    print_step(2, "Publish QuerySignal Events to Redis Streams")
    
    queries = [
        "Who is Chris Mansolillo?",
        "What projects has Chris Mansolillo worked on?",
        "Chris Mansolillo contact information"
    ]
    
    message_ids = []
    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}/{len(queries)}:")
        msg_id = publish_query_signal(TEST_ENTITY_ID, TEST_ENTITY_NAME, query)
        message_ids.append(msg_id)
        time.sleep(0.5)  # Small delay between events
    
    print(f"\n✅ Published {len(queries)} QuerySignal events")
    
    # Step 3: Wait for background worker to process
    print_step(3, "Wait for Background Worker to Process Events")
    
    print("Waiting 10 seconds for worker to consume and process events...")
    for i in range(10, 0, -1):
        print(f"  {i}...", end='\r')
        time.sleep(1)
    print("  Done!   ")
    
    # Step 4: Verify PostgreSQL update
    print_step(4, "Verify PostgreSQL Update")
    
    expected_score = len(queries)  # Each query adds 1 to demand_score
    postgres_updated = verify_postgres_update(TEST_ENTITY_ID, expected_score)
    
    # Step 5: Check analytics endpoints
    print_step(5, "Verify Analytics Endpoints Reflect Changes")
    
    updated_entity = get_entity_demand(TEST_ENTITY_ID)
    updated_stats = get_overall_stats()
    
    if updated_entity:
        print(f"Entity Demand Score: {updated_entity['demand_score']} (was {baseline_entity['demand_score']})")
        print(f"Entity Query Count: {updated_entity['query_count']} (was {baseline_entity['query_count']})")
        print(f"Last Queried: {updated_entity['last_queried_at']}")
        print(f"Query Frequency: {updated_entity['query_frequency']}")
        
        score_increased = updated_entity['demand_score'] > baseline_entity['demand_score']
        count_increased = updated_entity['query_count'] > baseline_entity['query_count']
        
        if score_increased and count_increased:
            print(f"\n✅ Entity metrics updated successfully!")
        else:
            print(f"\n⚠️  Entity metrics not yet updated")
    
    if updated_stats:
        print(f"\nOverall Stats:")
        print(f"  Total Queries: {updated_stats['total_queries']} (was {baseline_stats['total_queries']})")
        print(f"  Entities with Demand: {updated_stats['entities_with_demand']} (was {baseline_stats['entities_with_demand']})")
        print(f"  Avg Demand Score: {updated_stats['avg_demand_score']:.2f} (was {baseline_stats['avg_demand_score']:.2f})")
    
    # Step 6: Test top entities endpoint
    print_step(6, "Verify Top Entities Endpoint")
    
    top_url = f"{BACKEND_URL}/api/analytics/demand/top?limit=5"
    response = requests.get(top_url)
    
    if response.status_code == 200:
        top_data = response.json()
        print(f"Top {len(top_data['entities'])} entities by demand:")
        
        for i, entity in enumerate(top_data['entities'], 1):
            print(f"  {i}. {entity['name']} - Score: {entity['demand_score']}, Queries: {entity['query_count']}")
            
            if entity['id'] == TEST_ENTITY_ID:
                print(f"     ✅ Test entity found in top results!")
    
    # Final Summary
    print_section("TEST SUMMARY")
    
    success = True
    
    print("✅ Step 1: Baseline metrics retrieved")
    print("✅ Step 2: QuerySignal events published to Redis Streams")
    print("✅ Step 3: Waited for background worker processing")
    
    if postgres_updated:
        print("✅ Step 4: PostgreSQL updated correctly")
    else:
        print("⚠️  Step 4: PostgreSQL not yet updated (worker may need more time)")
        success = False
    
    if updated_entity and updated_entity['demand_score'] > baseline_entity['demand_score']:
        print("✅ Step 5: Analytics endpoints reflect changes")
    else:
        print("⚠️  Step 5: Analytics endpoints not yet updated")
        success = False
    
    print("✅ Step 6: Top entities endpoint tested")
    
    print("\n" + "="*80)
    if success:
        print("  ✅ INTEGRATION TEST PASSED")
        print("  All components working together correctly!")
    else:
        print("  ⚠️  INTEGRATION TEST INCOMPLETE")
        print("  Background worker may need more time to process events.")
        print("  Try running this test again in 1-2 minutes.")
    print("="*80 + "\n")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

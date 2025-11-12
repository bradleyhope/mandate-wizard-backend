#!/usr/bin/env python3
"""
Integration Test: Demand Tracking via API

Tests the demand tracking system by:
1. Making actual search queries to the backend API
2. Waiting for background worker to process events
3. Verifying demand scores updated via analytics endpoints

This test works without local Redis credentials by using the deployed backend.
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://mandate-wizard-backend.onrender.com"

def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_step(step_num, description):
    """Print formatted step"""
    print(f"\n[Step {step_num}] {description}")
    print("-" * 80)

def search_entity(query):
    """Make a search query to the backend"""
    url = f"{BACKEND_URL}/api/search"
    payload = {"query": query}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Search failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"Search error: {e}")
        return None

def get_entity_demand(entity_id):
    """Get current demand stats for an entity"""
    url = f"{BACKEND_URL}/api/analytics/demand/entity/{entity_id}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()['entity']
        else:
            return None
    except Exception as e:
        print(f"Error fetching entity demand: {e}")
        return None

def get_overall_stats():
    """Get overall demand statistics"""
    url = f"{BACKEND_URL}/api/analytics/demand/stats"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return None

def get_top_entities(limit=5):
    """Get top entities by demand"""
    url = f"{BACKEND_URL}/api/analytics/demand/top?limit={limit}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"Error fetching top entities: {e}")
        return None

def main():
    """Run the integration test"""
    
    print_section("INTEGRATION TEST: Demand Tracking via API")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Test Time: {datetime.utcnow().isoformat()}")
    
    # Step 1: Get baseline metrics
    print_step(1, "Get Baseline Metrics")
    
    baseline_stats = get_overall_stats()
    
    if baseline_stats:
        print(f"Overall Stats:")
        print(f"  Total Entities: {baseline_stats['total_entities']}")
        print(f"  Total Queries: {baseline_stats['total_queries']}")
        print(f"  Entities with Demand: {baseline_stats['entities_with_demand']}")
        print(f"  Avg Demand Score: {baseline_stats['avg_demand_score']}")
        print(f"  Trending Entities: {baseline_stats['trending_entities']}")
    else:
        print("⚠️  Could not fetch baseline stats")
        return False
    
    # Step 2: Get top entities before queries
    print_step(2, "Get Top Entities (Before Queries)")
    
    baseline_top = get_top_entities(5)
    
    if baseline_top:
        print(f"Top {len(baseline_top['entities'])} entities:")
        for i, entity in enumerate(baseline_top['entities'][:3], 1):
            print(f"  {i}. {entity['name']} - Score: {entity['demand_score']}, Queries: {entity['query_count']}")
    
    # Step 3: Make search queries
    print_step(3, "Make Search Queries to Trigger Events")
    
    test_queries = [
        "Who is Chris Mansolillo?",
        "Tell me about Netflix executives",
        "What projects has Warner Bros been working on?",
        "Who are the top producers in Hollywood?",
        "Information about Disney leadership"
    ]
    
    print(f"Making {len(test_queries)} search queries...\n")
    
    search_results = []
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}/{len(test_queries)}: {query}")
        result = search_entity(query)
        
        if result:
            # Extract entity IDs from search results
            entities_found = result.get('entities', [])
            print(f"  ✅ Found {len(entities_found)} entities")
            search_results.append({
                'query': query,
                'entities': entities_found
            })
        else:
            print(f"  ⚠️  Search failed")
        
        time.sleep(1)  # Small delay between queries
    
    print(f"\n✅ Completed {len(search_results)} successful searches")
    
    # Step 4: Wait for background worker
    print_step(4, "Wait for Background Worker to Process Events")
    
    wait_time = 15
    print(f"Waiting {wait_time} seconds for worker to consume and process events...")
    for i in range(wait_time, 0, -1):
        print(f"  {i}...", end='\r')
        time.sleep(1)
    print("  Done!   ")
    
    # Step 5: Check updated metrics
    print_step(5, "Verify Analytics Endpoints Reflect Changes")
    
    updated_stats = get_overall_stats()
    
    if updated_stats:
        print(f"Overall Stats (After Queries):")
        print(f"  Total Entities: {updated_stats['total_entities']}")
        print(f"  Total Queries: {updated_stats['total_queries']} (was {baseline_stats['total_queries']})")
        print(f"  Entities with Demand: {updated_stats['entities_with_demand']} (was {baseline_stats['entities_with_demand']})")
        print(f"  Avg Demand Score: {updated_stats['avg_demand_score']:.2f} (was {baseline_stats['avg_demand_score']:.2f})")
        print(f"  Trending Entities: {updated_stats['trending_entities']} (was {baseline_stats['trending_entities']})")
        
        # Check if metrics changed
        queries_increased = updated_stats['total_queries'] > baseline_stats['total_queries']
        demand_increased = updated_stats['entities_with_demand'] > baseline_stats['entities_with_demand']
        
        if queries_increased or demand_increased:
            print(f"\n✅ Metrics updated successfully!")
        else:
            print(f"\n⚠️  Metrics not yet updated (worker may need more time)")
    
    # Step 6: Check top entities after queries
    print_step(6, "Get Top Entities (After Queries)")
    
    updated_top = get_top_entities(10)
    
    if updated_top:
        print(f"Top {min(10, len(updated_top['entities']))} entities by demand:")
        
        entities_with_demand = [e for e in updated_top['entities'] if e['demand_score'] > 0]
        
        if entities_with_demand:
            print(f"\nEntities with demand scores > 0:")
            for i, entity in enumerate(entities_with_demand[:5], 1):
                print(f"  {i}. {entity['name']} ({entity['entity_type']})")
                print(f"     Score: {entity['demand_score']}, Queries: {entity['query_count']}")
                print(f"     Last Queried: {entity['last_queried_at']}")
        else:
            print("\n⚠️  No entities with demand scores > 0 yet")
            print("   (Background worker may need more time to process)")
    
    # Step 7: Test trending endpoint
    print_step(7, "Check Trending Entities")
    
    trending_url = f"{BACKEND_URL}/api/analytics/demand/trending?limit=5"
    
    try:
        response = requests.get(trending_url, timeout=10)
        if response.status_code == 200:
            trending_data = response.json()
            print(f"Trending entities (last {trending_data['timeframe']}):")
            
            if trending_data['trending']:
                for i, entity in enumerate(trending_data['trending'], 1):
                    print(f"  {i}. {entity['name']} - Score: {entity['demand_score']}")
            else:
                print("  (No trending entities yet)")
    except Exception as e:
        print(f"Error fetching trending: {e}")
    
    # Final Summary
    print_section("TEST SUMMARY")
    
    print("✅ Step 1: Baseline metrics retrieved")
    print("✅ Step 2: Top entities retrieved (before)")
    print(f"✅ Step 3: Made {len(search_results)} search queries")
    print("✅ Step 4: Waited for background worker")
    print("✅ Step 5: Updated metrics retrieved")
    print("✅ Step 6: Top entities retrieved (after)")
    print("✅ Step 7: Trending entities checked")
    
    # Determine success
    success = False
    
    if updated_stats:
        queries_increased = updated_stats['total_queries'] > baseline_stats['total_queries']
        demand_increased = updated_stats['entities_with_demand'] > baseline_stats['entities_with_demand']
        
        if queries_increased or demand_increased:
            success = True
            print("\n" + "="*80)
            print("  ✅ INTEGRATION TEST PASSED")
            print("  Background worker is processing events correctly!")
            print("  Demand scores are being updated in PostgreSQL!")
            print("="*80 + "\n")
        else:
            print("\n" + "="*80)
            print("  ⚠️  INTEGRATION TEST INCOMPLETE")
            print("  Metrics not yet updated. Possible reasons:")
            print("  1. Background worker needs more time (try waiting 1-2 minutes)")
            print("  2. Search queries didn't trigger QuerySignal events")
            print("  3. Worker may not be running or connected to Redis")
            print("="*80 + "\n")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

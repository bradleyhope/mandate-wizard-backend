#!/usr/bin/env python3
"""
Comprehensive Testing Framework for Mandate Wizard V5
Tests all 12 personas across different query types with streaming support
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_RESULTS_FILE = "/home/ubuntu/mandate_wizard_test_results.json"

# 12 Personas with their test queries
PERSONAS = [
    {
        "id": 1,
        "name": "New Producer - Dating Show",
        "query": "Who do I pitch my dating show to?",
        "expected_intent": "ROUTING",
        "expected_executive": "Molly Ebinger"
    },
    {
        "id": 2,
        "name": "Established Producer - Korean Drama",
        "query": "Who handles Korean content at Netflix?",
        "expected_intent": "ROUTING",
        "expected_executive": "Minyoung Kim"
    },
    {
        "id": 3,
        "name": "Development Executive - UK Crime",
        "query": "Who should I contact about a British crime thriller?",
        "expected_intent": "ROUTING",
        "expected_region": "UK"
    },
    {
        "id": 4,
        "name": "Strategic Researcher - Recent Mandates",
        "query": "What are some recent mandates from Netflix?",
        "expected_intent": "STRATEGIC",
        "expected_executives": ["Brandon Riegg", "Dan Lin", "Peter Friedlander"]
    },
    {
        "id": 5,
        "name": "Genre Specialist - Procedural Dramas",
        "query": "What kind of procedural dramas does Netflix want?",
        "expected_intent": "STRATEGIC",
        "expected_genre": "procedural"
    },
    {
        "id": 6,
        "name": "International Producer - Spanish Content",
        "query": "Who do I pitch my Spanish series to?",
        "expected_intent": "ROUTING",
        "expected_region": "Spain"
    },
    {
        "id": 7,
        "name": "Documentary Filmmaker - True Crime",
        "query": "Who handles true crime documentaries?",
        "expected_intent": "ROUTING",
        "expected_format": "documentary"
    },
    {
        "id": 8,
        "name": "Comparative Researcher - Similar Projects",
        "query": "What projects are similar to Squid Game?",
        "expected_intent": "COMPARATIVE",
        "expected_reference": "Squid Game"
    },
    {
        "id": 9,
        "name": "Market Analyst - Regional Teams",
        "query": "Which regions does Netflix have content teams in?",
        "expected_intent": "MARKET_INFO",
        "expected_info_type": "regions"
    },
    {
        "id": 10,
        "name": "Follow-up Researcher - Specific Executive",
        "query": "Tell me more about Brandon Riegg's mandate",
        "expected_intent": "STRATEGIC",
        "expected_executive": "Brandon Riegg"
    },
    {
        "id": 11,
        "name": "Film Producer - Feature Films",
        "query": "Who do I pitch my feature film to at Netflix?",
        "expected_intent": "ROUTING",
        "expected_format": "film"
    },
    {
        "id": 12,
        "name": "Unscripted Producer - Competition Show",
        "query": "Who handles competition shows at Netflix?",
        "expected_intent": "ROUTING",
        "expected_format": "unscripted"
    }
]

def test_streaming_endpoint(query: str, session_id: str) -> Dict[str, Any]:
    """Test the streaming endpoint and collect results"""
    url = f"{BASE_URL}/ask_stream"
    payload = {
        "question": query,
        "session_id": session_id
    }
    
    result = {
        "query": query,
        "success": False,
        "error": None,
        "chunks_received": 0,
        "status_messages": [],
        "answer": "",
        "response_time": 0,
        "has_quotes": False,
        "has_projects": False,
        "has_followups": False
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=60)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(data_str)
                        
                        if data.get('type') == 'status':
                            result['status_messages'].append(data.get('message'))
                        
                        elif data.get('type') == 'chunk':
                            result['chunks_received'] += 1
                            result['answer'] += data.get('content', '')
                        
                        elif data.get('type') == 'quotes':
                            result['has_quotes'] = True
                        
                        elif data.get('type') == 'projects':
                            result['has_projects'] = True
                        
                        elif data.get('type') == 'followups':
                            result['has_followups'] = True
                        
                        elif data.get('type') == 'done':
                            result['success'] = True
                        
                        elif data.get('type') == 'error':
                            result['error'] = data.get('message')
                            result['success'] = False
                            break
                    
                    except json.JSONDecodeError:
                        continue
        
        result['response_time'] = time.time() - start_time
        
    except requests.exceptions.Timeout:
        result['error'] = "Request timeout after 60 seconds"
    except requests.exceptions.RequestException as e:
        result['error'] = f"Request error: {str(e)}"
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
    
    return result

def run_comprehensive_tests() -> Dict[str, Any]:
    """Run all persona tests and collect results"""
    print("=" * 80)
    print("MANDATE WIZARD V5 - COMPREHENSIVE TESTING FRAMEWORK")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing {len(PERSONAS)} personas with streaming support")
    print("=" * 80)
    print()
    
    all_results = {
        "test_run": {
            "timestamp": datetime.now().isoformat(),
            "total_personas": len(PERSONAS),
            "base_url": BASE_URL
        },
        "personas": []
    }
    
    passed = 0
    failed = 0
    
    for i, persona in enumerate(PERSONAS, 1):
        print(f"\n[{i}/{len(PERSONAS)}] Testing: {persona['name']}")
        print(f"Query: {persona['query']}")
        print("-" * 80)
        
        session_id = f"test_persona_{persona['id']}_{int(time.time())}"
        
        result = test_streaming_endpoint(persona['query'], session_id)
        
        # Evaluate result
        if result['success']:
            print(f"✅ SUCCESS")
            print(f"   Chunks received: {result['chunks_received']}")
            print(f"   Response time: {result['response_time']:.2f}s")
            print(f"   Status messages: {len(result['status_messages'])}")
            print(f"   Answer length: {len(result['answer'])} chars")
            print(f"   Has quotes: {result['has_quotes']}")
            print(f"   Has projects: {result['has_projects']}")
            print(f"   Has follow-ups: {result['has_followups']}")
            
            # Show first 200 chars of answer
            if result['answer']:
                preview = result['answer'][:200].replace('\n', ' ')
                print(f"   Answer preview: {preview}...")
            
            passed += 1
        else:
            print(f"❌ FAILED")
            print(f"   Error: {result['error']}")
            failed += 1
        
        # Add to results
        persona_result = {
            **persona,
            **result
        }
        all_results['personas'].append(persona_result)
        
        # Small delay between tests
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(PERSONAS)}")
    print(f"Passed: {passed} ({passed/len(PERSONAS)*100:.1f}%)")
    print(f"Failed: {failed} ({failed/len(PERSONAS)*100:.1f}%)")
    print()
    
    # Calculate averages for successful tests
    successful_results = [r for r in all_results['personas'] if r['success']]
    if successful_results:
        avg_chunks = sum(r['chunks_received'] for r in successful_results) / len(successful_results)
        avg_time = sum(r['response_time'] for r in successful_results) / len(successful_results)
        avg_answer_length = sum(len(r['answer']) for r in successful_results) / len(successful_results)
        
        print("PERFORMANCE METRICS (Successful Tests)")
        print("-" * 80)
        print(f"Average chunks per response: {avg_chunks:.1f}")
        print(f"Average response time: {avg_time:.2f}s")
        print(f"Average answer length: {avg_answer_length:.0f} chars")
        print()
    
    # Feature adoption
    quotes_count = sum(1 for r in all_results['personas'] if r.get('has_quotes'))
    projects_count = sum(1 for r in all_results['personas'] if r.get('has_projects'))
    followups_count = sum(1 for r in all_results['personas'] if r.get('has_followups'))
    
    print("FEATURE ADOPTION")
    print("-" * 80)
    print(f"Responses with quotes: {quotes_count}/{len(PERSONAS)} ({quotes_count/len(PERSONAS)*100:.1f}%)")
    print(f"Responses with projects: {projects_count}/{len(PERSONAS)} ({projects_count/len(PERSONAS)*100:.1f}%)")
    print(f"Responses with follow-ups: {followups_count}/{len(PERSONAS)} ({followups_count/len(PERSONAS)*100:.1f}%)")
    print()
    
    # Save results
    all_results['summary'] = {
        "total": len(PERSONAS),
        "passed": passed,
        "failed": failed,
        "pass_rate": passed / len(PERSONAS) * 100
    }
    
    if successful_results:
        all_results['performance'] = {
            "avg_chunks": avg_chunks,
            "avg_response_time": avg_time,
            "avg_answer_length": avg_answer_length
        }
    
    all_results['features'] = {
        "quotes_count": quotes_count,
        "projects_count": projects_count,
        "followups_count": followups_count
    }
    
    with open(TEST_RESULTS_FILE, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"Results saved to: {TEST_RESULTS_FILE}")
    print("=" * 80)
    
    return all_results

if __name__ == "__main__":
    try:
        results = run_comprehensive_tests()
        
        # Exit with appropriate code
        if results['summary']['failed'] == 0:
            print("\n✅ All tests passed!")
            exit(0)
        else:
            print(f"\n⚠️  {results['summary']['failed']} test(s) failed")
            exit(1)
    
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Test framework error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


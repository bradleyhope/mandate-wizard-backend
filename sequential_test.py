#!/usr/bin/env python3
"""
Sequential Test - Run tests one at a time with detailed analysis
"""

import requests
import json
import time

def test_single_query(question, test_name, expected_executive=None):
    """Test a single query"""
    print(f"\n{'='*80}")
    print(f"TEST {test_name}")
    print(f"QUERY: {question}")
    print(f"{'='*80}")
    
    start = time.time()
    
    try:
        response = requests.post(
            "http://localhost:5000/ask_pathway",
            json={"question": question, "user_id": f"test_{test_name}"},
            timeout=120
        )
        
        elapsed = time.time() - start
        
        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            print(response.text[:500])
            return None
        
        data = response.json()
        
        if not data.get('success'):
            print(f"❌ Error: {data.get('error')}")
            return None
        
        # Print results
        print(f"\n⏱️  Time: {elapsed:.2f}s")
        print(f"👤 Executive: {data.get('executive_name')}")
        print(f"🎭 Persona: {data['user_profile']['persona']} ({data['user_profile']['sophistication_level']})")
        print(f"🎯 Confidence: {data['confidence_score']}")
        print(f"📝 Answer ({len(data['answer'])} chars):")
        print(data['answer'][:400] + "..." if len(data['answer']) > 400 else data['answer'])
        print(f"\n💡 Follow-ups ({len(data['follow_ups'])}):")
        for i, fu in enumerate(data['follow_ups'][:5], 1):
            print(f"  {i}. {fu}")
        
        # Check issues
        issues = []
        if elapsed > 30:
            issues.append(f"SLOW: {elapsed:.2f}s")
        if expected_executive and data.get('executive_name') != expected_executive:
            issues.append(f"WRONG EXEC: got {data.get('executive_name')}, expected {expected_executive}")
        if data.get('executive_name') == "Unknown":
            issues.append("NO EXEC NAME")
        if len(data['answer']) < 100:
            issues.append(f"TOO SHORT: {len(data['answer'])} chars")
        if len(data['follow_ups']) < 2:
            issues.append(f"FEW FOLLOWUPS: {len(data['follow_ups'])}")
        if data['confidence_score'] < 0.5:
            issues.append(f"LOW CONFIDENCE: {data['confidence_score']}")
        
        if issues:
            print(f"\n⚠️  Issues: {', '.join(issues)}")
        else:
            print(f"\n✅ PERFECT")
        
        return data
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

# Run tests
print("SEQUENTIAL STRESS TEST - 10 Critical Tests")
print("="*80)

test_single_query("Who handles Korean content?", "1", "Don Kang")
test_single_query("I have 48 hours to pitch my Korean thriller. Who do I contact and what do they want?", "2", "Don Kang")
test_single_query("What does Don Kang look for?", "3", "Don Kang")
test_single_query("What production companies work with him?", "4", "Don Kang")
test_single_query("I'm a new screenwriter. How do I get to Netflix?", "5")
test_single_query("Who handles documentaries?", "6")
test_single_query("What has Don Kang greenlit recently?", "7", "Don Kang")
test_single_query("What's Netflix's Korean content strategy?", "8", "Don Kang")
test_single_query("How do I pitch to Don Kang?", "9", "Don Kang")
test_single_query("What are typical budgets for Korean series?", "10", "Don Kang")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)


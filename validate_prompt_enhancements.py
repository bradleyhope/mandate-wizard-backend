#!/usr/bin/env python3
"""
Quick Validation Test - Post-Prompt Enhancement
Tests if production company recommendations and senior executive intelligence now surface
"""

import json
import requests
import time

# Test queries designed to trigger the enhanced prompts
test_queries = [
    {
        "id": 1,
        "query": "I'm a showrunner with a political thriller limited series. Who should I pitch to at Netflix?",
        "expected": ["production company", "prodco", "partner with", "littlefield", "aggregate"],
        "focus": "Production company recommendations (ROUTING)"
    },
    {
        "id": 2,
        "query": "I have a $50M overall deal offer from Netflix and Apple. Who makes the final decision at Netflix for deals this size?",
        "expected": ["bela bajaria", "chief content officer"],
        "focus": "Senior executive intelligence (STRATEGIC)"
    },
    {
        "id": 3,
        "query": "I want to adapt my bestselling thriller novel for Netflix. What's the process?",
        "expected": ["production company", "tomorrow studios", "picturestart", "partner with"],
        "focus": "Production company recommendations (PROCEDURAL)"
    },
    {
        "id": 4,
        "query": "I'm an A-list actor who wants to produce a prestige limited series. What are my chances of getting it greenlit?",
        "expected": ["70%", "greenlight rate", "success", "formula", "50%"],
        "focus": "Success formulas (PROCEDURAL)"
    }
]

print("=" * 80)
print("QUICK VALIDATION TEST - POST-PROMPT ENHANCEMENT")
print("=" * 80)
print("Testing if enhanced prompts surface:")
print("  1. Production company recommendations")
print("  2. Senior executive intelligence (Bela Bajaria, Peter Friedlander)")
print("  3. Success formulas")
print()

results = []

for test in test_queries:
    print(f"TEST {test['id']}/4")
    print("=" * 80)
    print(f"FOCUS: {test['focus']}")
    print(f"QUERY: {test['query']}")
    print("=" * 80)
    print("ANSWER:")
    print("-" * 80)
    
    start_time = time.time()
    
    try:
        response = requests.post(
            'http://localhost:5000/ask_stream',
            json={
                'question': test['query'],
                'session_id': f'validation_test_{test["id"]}'
            },
            stream=True,
            timeout=90
        )
        
        full_answer = ""
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        
                        if data['type'] == 'chunk':
                            content = data['content']
                            print(content, end='', flush=True)
                            full_answer += content
                        elif data['type'] == 'done':
                            print("\n[DONE]")
                    except json.JSONDecodeError:
                        pass
        
        elapsed = time.time() - start_time
        
        # Check if expected keywords appear
        answer_lower = full_answer.lower()
        found_keywords = [kw for kw in test['expected'] if kw in answer_lower]
        
        print("-" * 80)
        if found_keywords:
            print(f"✅ SUCCESS: Found {len(found_keywords)}/{len(test['expected'])} expected keywords")
            print(f"   Keywords found: {', '.join(found_keywords)}")
        else:
            print(f"❌ FAIL: None of the expected keywords found")
            print(f"   Expected: {', '.join(test['expected'])}")
        
        print(f"⏱️  Response time: {elapsed:.1f}s")
        
        results.append({
            'test_id': test['id'],
            'focus': test['focus'],
            'query': test['query'],
            'answer': full_answer,
            'found_keywords': found_keywords,
            'success': len(found_keywords) > 0,
            'response_time': elapsed
        })
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        results.append({
            'test_id': test['id'],
            'focus': test['focus'],
            'error': str(e),
            'success': False
        })
    
    print()
    
    if test['id'] < len(test_queries):
        print("Waiting 3 seconds before next query...")
        print()
        time.sleep(3)

# Summary
print("=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)

successful = sum(1 for r in results if r.get('success', False))
print(f"Successful Tests: {successful}/{len(results)}")
print()

print("BREAKDOWN BY FOCUS:")
print("-" * 80)
for result in results:
    status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
    print(f"{status}: {result['focus']}")
    if result.get('found_keywords'):
        print(f"       Found: {', '.join(result['found_keywords'])}")
print()

if successful >= 3:
    print("🎉 VALIDATION PASSED: Enhanced prompts are working!")
elif successful >= 2:
    print("⚠️  PARTIAL SUCCESS: Some enhancements working, needs more tuning")
else:
    print("❌ VALIDATION FAILED: Enhancements not surfacing as expected")

print("=" * 80)

# Save results
output_file = f"validation_results_{int(time.time())}.json"
with open(output_file, 'w') as f:
    json.dump({
        'test_suite': 'Prompt Enhancement Validation',
        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'total_tests': len(results),
            'successful': successful,
            'success_rate': successful / len(results) * 100
        },
        'results': results
    }, f, indent=2)

print(f"\n✅ Results saved to: {output_file}")


#!/usr/bin/env python3
"""Quick validation test for all fixes"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

# Test cases that previously failed
test_cases = [
    {
        "name": "Basic routing (previously worked)",
        "question": "Who handles Korean content?",
        "expected_exec": "Don Kang",
        "expected_sources": True
    },
    {
        "name": "Crisis mode detection",
        "question": "I have 48 hours to pitch my Korean thriller. Who do I contact?",
        "expected_crisis": True,
        "expected_exec": "Don Kang"
    },
    {
        "name": "Spanish content (previously worked)",
        "question": "Who handles Spanish-language content?",
        "expected_exec": "Francisco Ramos"
    },
    {
        "name": "Documentary query (previously failed - layer2 error)",
        "question": "Who greenlights documentaries at Netflix?",
        "expected_sources": True
    },
    {
        "name": "Unscripted query (previously failed - layer5 error)",
        "question": "What's the pitch process for reality shows?",
        "expected_sources": True
    }
]

print("=" * 70)
print("QUICK VALIDATION TEST - All Fixes")
print("=" * 70)

results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}

for i, test in enumerate(test_cases, 1):
    print(f"\n[{i}/{len(test_cases)}] {test['name']}")
    print(f"Question: {test['question']}")
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/ask_pathway",
            json={"question": test['question'], "user_id": f"test_{i}"},
            timeout=120
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                # Check expectations
                passed = True
                issues = []
                
                # Check executive name
                if 'expected_exec' in test:
                    exec_name = data.get('executive_name', 'Unknown')
                    if exec_name != test['expected_exec']:
                        passed = False
                        issues.append(f"Expected exec '{test['expected_exec']}', got '{exec_name}'")
                
                # Check sources
                if test.get('expected_sources'):
                    sources_count = len(data.get('sources', []))
                    if sources_count == 0:
                        passed = False
                        issues.append(f"Expected sources, got 0")
                
                # Check crisis mode
                if test.get('expected_crisis'):
                    crisis_mode = data.get('user_profile', {}).get('crisis_mode', False)
                    if not crisis_mode:
                        passed = False
                        issues.append(f"Expected crisis mode=True, got {crisis_mode}")
                
                if passed:
                    print(f"✅ PASSED ({elapsed:.1f}s)")
                    print(f"   Executive: {data.get('executive_name')}")
                    print(f"   Sources: {len(data.get('sources', []))}")
                    results['passed'] += 1
                else:
                    print(f"⚠️  PARTIAL PASS ({elapsed:.1f}s)")
                    for issue in issues:
                        print(f"   - {issue}")
                    results['passed'] += 0.5
                    results['failed'] += 0.5
            else:
                print(f"❌ FAILED: {data.get('error')}")
                results['failed'] += 1
                results['errors'].append({
                    'test': test['name'],
                    'error': data.get('error')
                })
        else:
            print(f"❌ HTTP {response.status_code}")
            results['failed'] += 1
            results['errors'].append({
                'test': test['name'],
                'error': f"HTTP {response.status_code}"
            })
            
    except requests.exceptions.Timeout:
        print(f"❌ TIMEOUT (>120s)")
        results['failed'] += 1
        results['errors'].append({
            'test': test['name'],
            'error': 'Timeout'
        })
    except Exception as e:
        print(f"❌ ERROR: {e}")
        results['failed'] += 1
        results['errors'].append({
            'test': test['name'],
            'error': str(e)
        })

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"✅ Passed: {results['passed']}/{len(test_cases)}")
print(f"❌ Failed: {results['failed']}/{len(test_cases)}")

if results['errors']:
    print("\nErrors:")
    for err in results['errors']:
        print(f"  - {err['test']}: {err['error']}")

print("\n" + "=" * 70)


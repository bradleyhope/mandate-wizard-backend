#!/usr/bin/env python3
"""
Comprehensive Persona Testing - Post-Enhancement
Tests competitive intelligence and packaging best practices surfacing
"""

import json
import requests
import time
from datetime import datetime

# Load test scenarios
with open('comprehensive_persona_tests.json', 'r') as f:
    test_data = json.load(f)

personas = test_data['personas']

# Results storage
results = []

print("=" * 80)
print("MANDATE WIZARD - COMPREHENSIVE PERSONA TESTING (POST-ENHANCEMENT)")
print("=" * 80)
print(f"Testing {len(personas)} sophisticated client scenarios")
print(f"Focus: {', '.join(test_data['focus_areas'])}")
print()

for i, persona in enumerate(personas, 1):
    print(f"TEST {i}/{len(personas)}")
    print("=" * 80)
    print(f"PERSONA: {persona['persona']}")
    print(f"BACKGROUND: {persona['background']}")
    print(f"QUERY: {persona['query']}")
    print("=" * 80)
    print("STREAMING RESPONSE:")
    print("-" * 80)
    
    start_time = time.time()
    
    # Make request
    try:
        response = requests.post(
            'http://localhost:5000/ask_stream',
            json={
                'question': persona['query'],
                'session_id': f'comprehensive_test_{i}'
            },
            stream=True,
            timeout=120
        )
        
        full_answer = ""
        followups = []
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        
                        if data['type'] == 'status':
                            print(f"[STATUS] {data['message']}")
                        elif data['type'] == 'chunk':
                            content = data['content']
                            print(content, end='', flush=True)
                            full_answer += content
                        elif data['type'] == 'followups':
                            followups = data.get('data', [])
                        elif data['type'] == 'done':
                            print("\n[DONE]")
                        elif data['type'] == 'error':
                            print(f"\n[ERROR] {data.get('message', 'Unknown error')}")
                    except json.JSONDecodeError:
                        pass
        
        elapsed = time.time() - start_time
        
        # Analyze answer against success criteria
        success_count = 0
        total_criteria = len(persona['success_criteria'])
        
        print("-" * 80)
        print("ANALYSIS:")
        print("-" * 80)
        
        for criterion in persona['success_criteria']:
            # Simple keyword matching for automated analysis
            criterion_lower = criterion.lower()
            answer_lower = full_answer.lower()
            
            # Check if key concepts from criterion appear in answer
            passed = False
            
            if 'mentions' in criterion_lower or 'identifies' in criterion_lower or 'provides' in criterion_lower:
                # Extract key terms to look for
                if 'netflix vs' in criterion_lower or 'compares' in criterion_lower:
                    if ('apple' in answer_lower or 'amazon' in answer_lower or 'hbo' in answer_lower):
                        passed = True
                elif 'timeline' in criterion_lower:
                    if ('weeks' in answer_lower or 'months' in answer_lower):
                        passed = True
                elif 'prodco' in criterion_lower or 'production company' in criterion_lower:
                    if ('production' in answer_lower and 'company' in answer_lower):
                        passed = True
                elif 'packaging' in criterion_lower:
                    if ('showrunner' in answer_lower or 'attach' in answer_lower or 'package' in answer_lower):
                        passed = True
                else:
                    # Generic check - if any significant word from criterion appears
                    words = [w for w in criterion_lower.split() if len(w) > 4]
                    if any(w in answer_lower for w in words):
                        passed = True
            
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {criterion}")
            if passed:
                success_count += 1
        
        success_rate = (success_count / total_criteria * 100) if total_criteria > 0 else 0
        
        print("-" * 80)
        print(f"✅ SUCCESS RATE: {success_count}/{total_criteria} ({success_rate:.0f}%)")
        print(f"⏱️  RESPONSE TIME: {elapsed:.1f}s")
        
        if followups:
            print(f"💡 FOLLOW-UPS: {len(followups)}")
            for fu in followups[:3]:
                print(f"  • {fu}")
        
        # Store results
        results.append({
            'persona_id': persona['id'],
            'persona': persona['persona'],
            'query': persona['query'],
            'answer': full_answer,
            'success_count': success_count,
            'total_criteria': total_criteria,
            'success_rate': success_rate,
            'response_time': elapsed,
            'followups': followups
        })
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        results.append({
            'persona_id': persona['id'],
            'persona': persona['persona'],
            'query': persona['query'],
            'error': str(e),
            'success_rate': 0
        })
    
    print()
    
    # Wait between queries
    if i < len(personas):
        print("Waiting 5 seconds before next query...")
        print()
        time.sleep(5)

# Summary
print("=" * 80)
print("COMPREHENSIVE TEST SUMMARY")
print("=" * 80)

successful_tests = [r for r in results if 'error' not in r and r['success_rate'] > 50]
avg_success_rate = sum(r['success_rate'] for r in results if 'error' not in r) / len([r for r in results if 'error' not in r]) if results else 0
avg_response_time = sum(r.get('response_time', 0) for r in results if 'error' not in r) / len([r for r in results if 'error' not in r]) if results else 0

print(f"Total Tests: {len(results)}")
print(f"Successful Tests (>50% criteria met): {len(successful_tests)}/{len(results)}")
print(f"Average Success Rate: {avg_success_rate:.1f}%")
print(f"Average Response Time: {avg_response_time:.1f}s")
print()

# Breakdown by focus area
print("INTELLIGENCE SURFACING BREAKDOWN:")
print("-" * 80)

competitive_intel_count = sum(1 for r in results if 'error' not in r and ('apple' in r.get('answer', '').lower() or 'amazon' in r.get('answer', '').lower() or 'hbo' in r.get('answer', '').lower()))
packaging_intel_count = sum(1 for r in results if 'error' not in r and ('showrunner' in r.get('answer', '').lower() or 'package' in r.get('answer', '').lower()))
timeline_intel_count = sum(1 for r in results if 'error' not in r and ('weeks' in r.get('answer', '').lower() or 'months' in r.get('answer', '').lower()))
prodco_intel_count = sum(1 for r in results if 'error' not in r and 'production company' in r.get('answer', '').lower())

print(f"Competitive Intelligence: {competitive_intel_count}/{len(results)} answers ({competitive_intel_count/len(results)*100:.0f}%)")
print(f"Packaging Best Practices: {packaging_intel_count}/{len(results)} answers ({packaging_intel_count/len(results)*100:.0f}%)")
print(f"Timeline Expectations: {timeline_intel_count}/{len(results)} answers ({timeline_intel_count/len(results)*100:.0f}%)")
print(f"Production Company Recs: {prodco_intel_count}/{len(results)} answers ({prodco_intel_count/len(results)*100:.0f}%)")
print()

# Save results
output_file = f"comprehensive_test_results_{int(time.time())}.json"
with open(output_file, 'w') as f:
    json.dump({
        'test_suite': test_data['test_suite'],
        'date': datetime.now().isoformat(),
        'summary': {
            'total_tests': len(results),
            'successful_tests': len(successful_tests),
            'avg_success_rate': avg_success_rate,
            'avg_response_time': avg_response_time,
            'competitive_intel_coverage': competitive_intel_count / len(results) * 100,
            'packaging_intel_coverage': packaging_intel_count / len(results) * 100,
            'timeline_intel_coverage': timeline_intel_count / len(results) * 100,
            'prodco_intel_coverage': prodco_intel_count / len(results) * 100
        },
        'results': results
    }, f, indent=2)

print(f"✅ Results saved to: {output_file}")
print("=" * 80)


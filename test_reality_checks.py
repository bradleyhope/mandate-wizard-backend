#!/usr/bin/env python3
"""
Reality Check Validation - Tests if system sets realistic expectations
"""

import json, requests, time

queries = [
    {
        'query': 'I have a great idea for a Netflix show. What are my chances?',
        'expected_reality': ['1-2%', 'long odds', 'difficult', 'most pitches', 'competition', 'backup plan'],
        'focus': 'Honest success rates'
    },
    {
        'query': 'I want to pitch my true crime podcast to Netflix. How likely is it to get greenlit?',
        'expected_reality': ['1-2 true crime', 'per year', 'thousands', 'selective', 'long odds', 'difficult'],
        'focus': 'Market selectivity reality'
    },
    {
        'query': 'I am a first-time creator. Can I get my project on Netflix?',
        'expected_reality': ['difficult', 'track record', 'production company', 'long odds', 'backup', 'most projects'],
        'focus': 'First-timer reality check'
    }
]

print('=' * 80)
print('REALITY CHECK VALIDATION TEST')
print('=' * 80)
print('Testing if system sets brutally honest expectations about greenlight difficulty')
print()

results = []

for i, test in enumerate(queries, 1):
    print(f'TEST {i}/3')
    print('=' * 80)
    print(f'FOCUS: {test["focus"]}')
    print(f'QUERY: {test["query"]}')
    print('=' * 80)
    print('ANSWER:')
    print('-' * 80)
    
    resp = requests.post('http://localhost:5000/ask_stream', 
                         json={'question': test['query'], 'session_id': f'reality_{i}'}, 
                         stream=True, timeout=90)
    
    answer = ''
    for line in resp.iter_lines():
        if line and line.decode('utf-8').startswith('data: '):
            try:
                data = json.loads(line.decode('utf-8')[6:])
                if data['type'] == 'chunk':
                    content = data['content']
                    print(content, end='', flush=True)
                    answer += content
                elif data['type'] == 'done':
                    print('\n[DONE]')
            except:
                pass
    
    # Check for reality check keywords
    answer_lower = answer.lower()
    found_reality = [kw for kw in test['expected_reality'] if kw in answer_lower]
    
    has_reality_check = len(found_reality) > 0
    
    print('-' * 80)
    if has_reality_check:
        print(f'✅ REALITY CHECK PRESENT: Found {len(found_reality)} reality keywords')
        print(f'   Keywords: {", ".join(found_reality)}')
    else:
        print(f'❌ NO REALITY CHECK: None of the expected reality keywords found')
        print(f'   Expected: {", ".join(test["expected_reality"])}')
    
    results.append({
        'query': test['query'],
        'focus': test['focus'],
        'has_reality_check': has_reality_check,
        'found_reality': found_reality,
        'answer': answer
    })
    
    print()
    
    if i < len(queries):
        print('Waiting 3 seconds...')
        print()
        time.sleep(3)

print('=' * 80)
print('SUMMARY')
print('=' * 80)

reality_count = sum(1 for r in results if r['has_reality_check'])
print(f'Answers with Reality Checks: {reality_count}/{len(results)} ({reality_count/len(results)*100:.0f}%)')
print()

for r in results:
    status = '✅' if r['has_reality_check'] else '❌'
    print(f'{status} {r["focus"]}')
    if r['found_reality']:
        print(f'   Reality keywords: {", ".join(r["found_reality"])}')

print()
if reality_count >= 2:
    print('🎉 SUCCESS: System is setting realistic expectations!')
else:
    print('⚠️  System needs to be more honest about difficulty')

print('=' * 80)


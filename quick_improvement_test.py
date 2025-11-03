#!/usr/bin/env python3
import json, requests, time

queries = [
    'I have a breakout true crime podcast. What is the realistic path to Netflix?',
    'I am an A-list actor who wants to produce a prestige limited series. What do I need?',
    'I have a bestselling thriller book series. How do I get it adapted?'
]

print('QUICK IMPROVEMENT TEST - Production Company Recommendations')
print('=' * 80)

results = []

for i, q in enumerate(queries, 1):
    print(f'\nTest {i}: {q}')
    print('-' * 80)
    
    resp = requests.post('http://localhost:5000/ask_stream', 
                         json={'question': q, 'session_id': f'quick_{i}'}, 
                         stream=True, timeout=90)
    
    answer = ''
    for line in resp.iter_lines():
        if line and line.decode('utf-8').startswith('data: '):
            try:
                data = json.loads(line.decode('utf-8')[6:])
                if data['type'] == 'chunk':
                    answer += data['content']
            except:
                pass
    
    # Check for prodco recommendations
    answer_lower = answer.lower()
    prodco_keywords = ['production company', 'prodco', 'partner with', 'raw tv', 'campfire', 'tomorrow studios', 'picturestart', '21 laps', 'plan b', 'aggregate', 'littlefield']
    found_prodcos = [kw for kw in prodco_keywords if kw in answer_lower]
    
    has_prodco = len(found_prodcos) > 0
    has_timeline = any(x in answer_lower for x in ['weeks', 'months'])
    
    print(f'Production Company Rec: {"✅" if has_prodco else "❌"}')
    if found_prodcos:
        print(f'  Found: {", ".join(found_prodcos)}')
    print(f'Timeline Intelligence: {"✅" if has_timeline else "❌"}')
    
    results.append({
        'query': q,
        'has_prodco': has_prodco,
        'found_prodcos': found_prodcos,
        'has_timeline': has_timeline
    })
    
    if i < len(queries):
        time.sleep(3)

print('\n' + '=' * 80)
print('SUMMARY')
print('=' * 80)
prodco_count = sum(1 for r in results if r['has_prodco'])
timeline_count = sum(1 for r in results if r['has_timeline'])

print(f'Production Company Recommendations: {prodco_count}/{len(results)} ({prodco_count/len(results)*100:.0f}%)')
print(f'Timeline Intelligence: {timeline_count}/{len(results)} ({timeline_count/len(results)*100:.0f}%)')

if prodco_count >= 2:
    print('\n🎉 SUCCESS: Production company recommendations significantly improved!')
else:
    print('\n⚠️  Needs more work on production company recommendations')


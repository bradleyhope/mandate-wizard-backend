#!/usr/bin/env python3
"""Test if the system is honest but empowering (not depressing)"""

import json, requests, time

queries = [
    'I have a great idea for a Netflix show. What are my chances?',
    'I want to pitch my true crime podcast to Netflix. How likely is it to get greenlit?',
    'I am a first-time creator. Can I get my project on Netflix?'
]

print('=' * 80)
print('EMPOWERING TONE TEST')
print('=' * 80)
print('Testing if system is honest but empowering (not depressing)')
print()

for i, q in enumerate(queries, 1):
    print(f'TEST {i}/3: {q}')
    print('-' * 80)
    
    resp = requests.post('http://localhost:5000/ask_stream', 
                         json={'question': q, 'session_id': f'empowering_{i}'}, 
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
            except:
                pass
    
    print('\n' + '-' * 80)
    
    # Check for empowering language
    answer_lower = answer.lower()
    
    # Depressing indicators (we DON'T want these)
    depressing = ['long odds', 'most pitches', 'most projects', 'backup plan', 'sub-1%']
    found_depressing = [kw for kw in depressing if kw in answer_lower]
    
    # Empowering indicators (we DO want these)
    empowering = ['odds could jump', 'could jump as high as', 'significantly improve', 'dramatically improve', 'your chances', 'with the right', 'here\'s what moves']
    found_empowering = [kw for kw in empowering if kw in answer_lower]
    
    # Reality check (we want honest numbers)
    has_reality = any(x in answer_lower for x in ['1-2%', '1–2%', 'single digits'])
    
    if found_depressing:
        print(f'⚠️  DEPRESSING language found: {", ".join(found_depressing)}')
    
    if found_empowering:
        print(f'✅ EMPOWERING language found: {", ".join(found_empowering)}')
    
    if has_reality:
        print(f'✅ REALITY CHECK present (honest numbers)')
    
    if found_empowering and has_reality and not found_depressing:
        print(f'🎉 PERFECT: Honest + Empowering (not depressing)')
    elif found_empowering and not found_depressing:
        print(f'✅ GOOD: Empowering tone')
    elif found_depressing:
        print(f'❌ TOO DEPRESSING: Needs more empowering language')
    
    print()
    
    if i < len(queries):
        time.sleep(3)

print('=' * 80)


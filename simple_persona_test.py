#!/usr/bin/env python3
"""
Simple persona test - runs one query at a time with detailed output
"""

import requests
import json
import time

def test_query(question, session_id="test"):
    """Test a single query"""
    print(f"\n{'='*80}")
    print(f"QUESTION: {question}")
    print(f"{'='*80}\n")
    
    url = "http://localhost:5000/ask_stream"
    payload = {"question": question, "session_id": session_id}
    
    start_time = time.time()
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=90)
        
        answer_parts = []
        followups = []
        
        print("STREAMING RESPONSE:")
        print("-" * 80)
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    data_json = line_text[6:]
                    try:
                        data = json.loads(data_json)
                        
                        if data.get('type') == 'status':
                            print(f"[STATUS] {data.get('message')}")
                        elif data.get('type') == 'chunk':
                            chunk = data.get('content', '')
                            answer_parts.append(chunk)
                            print(chunk, end='', flush=True)
                        elif data.get('type') == 'answer':
                            answer_parts = [data.get('content', '')]
                            print(data.get('content', ''))
                        elif data.get('type') == 'followups':
                            followups = data.get('data', [])
                        elif data.get('type') == 'error':
                            print(f"\n[ERROR] {data.get('message')}")
                            return False
                        elif data.get('type') == 'done':
                            print("\n[DONE]")
                    except json.JSONDecodeError:
                        pass
        
        elapsed = time.time() - start_time
        
        print(f"\n{'-'*80}")
        print(f"✅ SUCCESS in {elapsed:.1f}s")
        
        if followups:
            print(f"\nFOLLOW-UPS:")
            for fu in followups:
                print(f"  • {fu}")
        
        return True
        
    except requests.exceptions.Timeout:
        elapsed = time.time() - start_time
        print(f"\n❌ TIMEOUT after {elapsed:.1f}s")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ ERROR after {elapsed:.1f}s: {e}")
        return False

# Test queries from sophisticated personas
test_queries = [
    # Persona 1: Established Showrunner
    "I have a political thriller limited series with an A-list lead attached. Who's the right Netflix executive to pitch this to, and what do they actually care about right now?",
    
    # Persona 2: A-List Actor
    "My overall deal is expiring and I'm considering Netflix. Who should I be talking to about a high-end true crime anthology series?",
    
    # Persona 3: International Producer  
    "I'm a UK producer with a climate sci-fi drama. Do I pitch to Netflix UK or Netflix US? Who's the right executive?",
    
    # Persona 5: Novelist
    "I'm a bestselling author and want to control the adaptation of my thriller series. Who at Netflix should I be talking to?",
]

print("\n" + "="*80)
print("MANDATE WIZARD - SIMPLE PERSONA TESTING")
print("="*80)
print(f"Testing {len(test_queries)} sophisticated client queries\n")

success_count = 0

for i, query in enumerate(test_queries, 1):
    print(f"\n\nTEST {i}/{len(test_queries)}")
    
    if test_query(query, session_id=f"persona_test_{i}"):
        success_count += 1
    
    if i < len(test_queries):
        print(f"\nWaiting 3 seconds before next query...")
        time.sleep(3)

print(f"\n\n{'='*80}")
print(f"RESULTS: {success_count}/{len(test_queries)} successful")
print(f"{'='*80}\n")


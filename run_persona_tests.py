#!/usr/bin/env python3
"""
Persona-Based Testing for Mandate Wizard
Tests sophisticated client scenarios with real project queries
"""

import json
import requests
import time
from datetime import datetime

def run_query(question, session_id="persona_test"):
    """Send query to Mandate Wizard and get response"""
    url = "http://localhost:5000/ask_stream"
    
    payload = {
        "question": question,
        "session_id": session_id
    }
    
    try:
        response = requests.post(url, json=payload, stream=True, timeout=120)
        
        # Collect streaming response
        full_answer = ""
        followups = []
        status_messages = []
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    data_json = line_text[6:]  # Remove 'data: ' prefix
                    try:
                        data = json.loads(data_json)
                        
                        if data.get('type') == 'chunk':
                            full_answer += data.get('content', '')
                        elif data.get('type') == 'answer':
                            full_answer = data.get('content', '')
                        elif data.get('type') == 'followups':
                            followups = data.get('data', [])
                        elif data.get('type') == 'status':
                            status_messages.append(data.get('message', ''))
                        elif data.get('type') == 'error':
                            return {
                                'success': False,
                                'error': data.get('message', 'Unknown error'),
                                'status_messages': status_messages
                            }
                    except json.JSONDecodeError:
                        continue
        
        return {
            'success': True,
            'answer': full_answer.strip(),
            'followups': followups,
            'status_messages': status_messages
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def evaluate_answer(answer, success_criteria):
    """Evaluate answer quality against success criteria"""
    score = 0
    max_score = len(success_criteria)
    matches = []
    
    answer_lower = answer.lower()
    
    for criterion in success_criteria:
        criterion_lower = criterion.lower()
        
        # Simple keyword matching for now
        # In production, would use more sophisticated NLP
        if any(keyword in answer_lower for keyword in criterion_lower.split()):
            score += 1
            matches.append(criterion)
    
    return {
        'score': score,
        'max_score': max_score,
        'percentage': (score / max_score * 100) if max_score > 0 else 0,
        'matched_criteria': matches
    }

def run_persona_test(persona, max_questions=3):
    """Run test for a single persona"""
    print(f"\n{'='*80}")
    print(f"PERSONA {persona['persona_id']}: {persona['name']}")
    print(f"{'='*80}")
    print(f"Background: {persona['background']}")
    print(f"Project: {persona['project']['title']} - {persona['project']['logline']}")
    print(f"Sophistication: {persona['sophistication']}")
    print(f"\n")
    
    results = []
    
    # Test first N questions
    questions_to_test = persona['questions'][:max_questions]
    
    for i, question in enumerate(questions_to_test, 1):
        print(f"\n{'-'*80}")
        print(f"QUESTION {i}/{len(questions_to_test)}:")
        print(f"{question}")
        print(f"{'-'*80}\n")
        
        start_time = time.time()
        
        # Run query
        result = run_query(question, session_id=f"persona_{persona['persona_id']}")
        
        elapsed_time = time.time() - start_time
        
        if result['success']:
            print(f"✅ SUCCESS ({elapsed_time:.1f}s)\n")
            print(f"ANSWER:")
            print(f"{result['answer']}\n")
            
            if result['followups']:
                print(f"FOLLOW-UPS:")
                for fu in result['followups']:
                    print(f"  • {fu}")
                print()
            
            # Evaluate against success criteria
            evaluation = evaluate_answer(result['answer'], persona['success_criteria'])
            
            print(f"EVALUATION:")
            print(f"  Score: {evaluation['score']}/{evaluation['max_score']} ({evaluation['percentage']:.0f}%)")
            if evaluation['matched_criteria']:
                print(f"  Matched criteria:")
                for criterion in evaluation['matched_criteria']:
                    print(f"    ✓ {criterion}")
            print()
            
            results.append({
                'question': question,
                'answer': result['answer'],
                'followups': result['followups'],
                'elapsed_time': elapsed_time,
                'evaluation': evaluation,
                'success': True
            })
        else:
            print(f"❌ FAILED ({elapsed_time:.1f}s)")
            print(f"ERROR: {result.get('error', 'Unknown error')}\n")
            
            results.append({
                'question': question,
                'error': result.get('error'),
                'elapsed_time': elapsed_time,
                'success': False
            })
        
        # Wait between questions
        if i < len(questions_to_test):
            time.sleep(2)
    
    return results

def main():
    """Run all persona tests"""
    print("\n" + "="*80)
    print("MANDATE WIZARD - SOPHISTICATED PERSONA TESTING")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load test scenarios
    with open('persona_test_scenarios.json', 'r') as f:
        data = json.load(f)
    
    personas = data['test_scenarios']
    
    print(f"Loaded {len(personas)} persona test scenarios")
    print(f"Testing first 3 questions per persona for speed")
    print()
    
    all_results = {}
    
    for persona in personas:
        results = run_persona_test(persona, max_questions=3)
        all_results[persona['persona_id']] = {
            'persona': persona['name'],
            'results': results
        }
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")
    
    total_questions = 0
    successful_questions = 0
    total_score = 0
    max_total_score = 0
    
    for persona_id, data in all_results.items():
        persona_name = data['persona']
        results = data['results']
        
        questions_count = len(results)
        success_count = sum(1 for r in results if r['success'])
        
        total_questions += questions_count
        successful_questions += success_count
        
        if success_count > 0:
            avg_score = sum(r['evaluation']['score'] for r in results if r['success']) / success_count
            avg_max = sum(r['evaluation']['max_score'] for r in results if r['success']) / success_count
            avg_pct = (avg_score / avg_max * 100) if avg_max > 0 else 0
            
            total_score += sum(r['evaluation']['score'] for r in results if r['success'])
            max_total_score += sum(r['evaluation']['max_score'] for r in results if r['success'])
            
            print(f"Persona {persona_id} ({persona_name}):")
            print(f"  Questions: {success_count}/{questions_count} successful")
            print(f"  Avg Score: {avg_score:.1f}/{avg_max:.1f} ({avg_pct:.0f}%)")
            print()
    
    overall_pct = (total_score / max_total_score * 100) if max_total_score > 0 else 0
    
    print(f"OVERALL:")
    print(f"  Total Questions: {successful_questions}/{total_questions} successful ({successful_questions/total_questions*100:.0f}%)")
    print(f"  Overall Score: {total_score}/{max_total_score} ({overall_pct:.0f}%)")
    print()
    
    # Save results
    output_file = f"persona_test_results_{int(time.time())}.json"
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"Results saved to: {output_file}")
    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    main()


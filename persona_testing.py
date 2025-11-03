#!/usr/bin/env python3
"""
Persona Testing Script
Runs deep testing sessions with realistic user personas
"""

import requests
import json
import time
from datetime import datetime

# Backend API URL
API_URL = "http://localhost:5000"

# Test personas with their queries
PERSONAS = {
    "sarah_chen_producer": {
        "name": "Sarah Chen - Independent Producer",
        "email": "sarah.chen@test.com",
        "queries": [
            "What is Netflix looking for in limited series right now?",
            "Tell me about Jinny Howe's taste and what she's buying",
            "What rom-coms got greenlit in the last 3 months?",
            "Are streamers still buying true crime documentaries?",
            "Which executives should I pitch my psychological thriller to?",
            "What are the top mandates for female-led dramas?",
            "Give me examples of recent greenlight deals for independent producers",
            "What's the competitive landscape for limited series at Apple TV+?",
            "Who are the rising executives I should know about?",
            "What production companies are hot right now for packaging?",
            "Is there a market for international co-productions?",
            "What budget ranges are streamers looking for in limited series?",
        ]
    },
    "marcus_williams_manager": {
        "name": "Marcus Williams - Literary Manager",
        "email": "marcus.williams@test.com",
        "queries": [
            "What shows are hiring writers right now?",
            "Where did Brandon Riegg move to and what is he buying?",
            "Is sci-fi selling better than it was last year?",
            "What is Apple TV+ looking for in their drama slate?",
            "Who else is developing shows about AI?",
            "What are the best opportunities for emerging writers?",
            "Which showrunners are known for developing new writers?",
            "What's the market like for comedy writers right now?",
            "Are there any open writing assignments for limited series?",
            "What production companies are actively looking for writers?",
            "Give me a list of executives who champion diverse voices",
            "What genres are oversaturated right now?",
        ]
    },
    "jennifer_park_development": {
        "name": "Jennifer Park - Development Executive",
        "email": "jennifer.park@test.com",
        "queries": [
            "What is Rideback developing right now?",
            "What did Netflix buy from Warner Bros recently?",
            "Who is Shonda Rhimes working with on her next project?",
            "Are anthology series still selling to streamers?",
            "Should we develop this as a limited series or ongoing?",
            "What are our competitors at [company name] working on?",
            "What's the success rate for book adaptations lately?",
            "Which buyers are most active in the thriller space?",
            "What deal terms are typical for first-look agreements?",
            "Are streamers cutting back on big-budget productions?",
            "What production companies have the best track record?",
            "Give me comps for a female-led action series",
        ]
    },
    "david_rodriguez_consultant": {
        "name": "David Rodriguez - Entertainment Consultant",
        "email": "david.rodriguez@test.com",
        "queries": [
            "Give me a comprehensive analysis of Netflix's drama strategy for 2025",
            "What genres will be hot in 2026 based on current trends?",
            "How does HBO's content strategy compare to Netflix?",
            "What are the top 10 executives buying drama series right now?",
            "How many limited series got greenlit this year vs last year?",
            "Analyze the shift in streaming content strategies over the past year",
            "What production companies are winning the most deals?",
            "Give me a market overview of the true crime documentary space",
            "What are the emerging trends in international content?",
            "How is the market for unscripted content evolving?",
            "What's the ROI on different content categories for streamers?",
            "Provide a competitive landscape analysis for prestige drama",
        ]
    },
    "amy_thompson_showrunner": {
        "name": "Amy Thompson - Showrunner",
        "email": "amy.thompson@test.com",
        "queries": [
            "Which streamer is the best fit for a dark comedy about grief?",
            "Who are the top drama executives at HBO?",
            "What shows like mine are currently in development?",
            "What kind of overall deals is Apple TV+ making with showrunners?",
            "Is now a good time to pitch a limited series to Netflix?",
            "Which executives have a track record of championing female showrunners?",
            "What are the key mandates I should know before pitching to Hulu?",
            "Give me examples of successful pitches for dark comedies",
            "What production companies should I partner with for my next show?",
            "How competitive is the market for limited series right now?",
            "What are the typical deal terms for showrunner overall deals?",
            "Which buyers are looking for elevated genre content?",
        ]
    },
    "michael_zhang_agent": {
        "name": "Michael Zhang - Talent Agent",
        "email": "michael.zhang@test.com",
        "queries": [
            "What projects are casting female leads in their 30s?",
            "Who's attached to direct the new Netflix limited series?",
            "What's going into production in Q1 2026?",
            "Who should I call about the new Apple TV+ drama?",
            "What is UTA packaging right now?",
            "Which directors are in high demand for limited series?",
            "What talent is attached to upcoming Netflix projects?",
            "Are there opportunities for my client who does action?",
            "What showrunners are looking for directors?",
            "Give me a list of projects in pre-production",
            "Which buyers are most receptive to talent-driven packages?",
            "What's the market like for mid-level directors?",
        ]
    },
    "lisa_martinez_analyst": {
        "name": "Lisa Martinez - Investment Analyst",
        "email": "lisa.martinez@test.com",
        "queries": [
            "What percentage of greenlights are limited series vs ongoing series?",
            "How many projects has Rideback sold this year?",
            "Is Netflix shifting away from big-budget content?",
            "What content categories are growing fastest?",
            "Are streamers cutting back on unscripted content?",
            "Give me data on the success rate of book adaptations",
            "What's the average deal size for production company first-looks?",
            "How has the market for international content evolved?",
            "What production companies are most valuable based on output?",
            "Analyze the ROI of different content strategies",
            "What's the trend in overall deal values for talent?",
            "Give me market sizing data for the streaming content market",
        ]
    }
}

def test_persona(persona_id, persona_data):
    """Test a persona with their queries"""
    print(f"\n{'='*80}")
    print(f"Testing: {persona_data['name']}")
    print(f"{'='*80}\n")
    
    results = {
        "persona": persona_data['name'],
        "email": persona_data['email'],
        "timestamp": datetime.now().isoformat(),
        "queries": []
    }
    
    for i, query in enumerate(persona_data['queries'], 1):
        print(f"\n[{i}/{len(persona_data['queries'])}] Query: {query}")
        print("-" * 80)
        
        start_time = time.time()
        
        try:
            # Make API request
            response = requests.post(
                f"{API_URL}/query",
                json={
                    "question": query,
                    "email": persona_data['email'],
                    "session_id": persona_id,
                    "subscription_status": "paid"
                },
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', 'No answer provided')
                
                print(f"✓ Success ({response_time:.2f}s)")
                print(f"\nAnswer: {answer[:500]}...")  # First 500 chars
                
                # Evaluate response quality
                quality_score = evaluate_response(query, answer)
                
                results['queries'].append({
                    "query": query,
                    "answer": answer,
                    "response_time": response_time,
                    "success": True,
                    "quality_score": quality_score,
                    "intent": data.get('intent', 'unknown')
                })
                
                print(f"Quality Score: {quality_score}/10")
                
            else:
                print(f"✗ Failed: HTTP {response.status_code}")
                print(f"Error: {response.text}")
                
                results['queries'].append({
                    "query": query,
                    "answer": None,
                    "response_time": response_time,
                    "success": False,
                    "error": response.text
                })
        
        except Exception as e:
            response_time = time.time() - start_time
            print(f"✗ Exception: {str(e)}")
            
            results['queries'].append({
                "query": query,
                "answer": None,
                "response_time": response_time,
                "success": False,
                "error": str(e)
            })
        
        # Rate limiting - wait between queries
        time.sleep(3)
    
    return results

def evaluate_response(query, answer):
    """Evaluate response quality (0-10)"""
    score = 5  # Base score
    
    # Length check (too short = bad)
    if len(answer) < 100:
        score -= 2
    elif len(answer) > 200:
        score += 1
    
    # Specificity check (mentions names, numbers, examples)
    if any(word in answer.lower() for word in ['netflix', 'hbo', 'apple', 'amazon', 'hulu']):
        score += 1
    
    # Actionability check (provides specific recommendations)
    if any(word in answer.lower() for word in ['should', 'recommend', 'suggest', 'consider']):
        score += 1
    
    # Context check (provides examples or context)
    if any(word in answer.lower() for word in ['example', 'for instance', 'such as', 'including']):
        score += 1
    
    # Vagueness penalty
    if any(phrase in answer.lower() for phrase in ['it depends', 'varies', 'not sure', 'unclear']):
        score -= 1
    
    return max(0, min(10, score))

def generate_summary(all_results):
    """Generate summary statistics"""
    print(f"\n\n{'='*80}")
    print("TESTING SUMMARY")
    print(f"{'='*80}\n")
    
    total_queries = 0
    successful_queries = 0
    total_response_time = 0
    total_quality_score = 0
    
    for persona_results in all_results:
        persona_name = persona_results['persona']
        queries = persona_results['queries']
        
        persona_success = sum(1 for q in queries if q['success'])
        persona_avg_time = sum(q['response_time'] for q in queries) / len(queries)
        persona_avg_quality = sum(q.get('quality_score', 0) for q in queries if q['success']) / max(persona_success, 1)
        
        print(f"{persona_name}:")
        print(f"  Success Rate: {persona_success}/{len(queries)} ({persona_success/len(queries)*100:.1f}%)")
        print(f"  Avg Response Time: {persona_avg_time:.2f}s")
        print(f"  Avg Quality Score: {persona_avg_quality:.1f}/10")
        print()
        
        total_queries += len(queries)
        successful_queries += persona_success
        total_response_time += persona_avg_time * len(queries)
        total_quality_score += sum(q.get('quality_score', 0) for q in queries if q['success'])
    
    print(f"\nOVERALL:")
    print(f"  Total Queries: {total_queries}")
    print(f"  Success Rate: {successful_queries}/{total_queries} ({successful_queries/total_queries*100:.1f}%)")
    print(f"  Avg Response Time: {total_response_time/total_queries:.2f}s")
    print(f"  Avg Quality Score: {total_quality_score/successful_queries:.1f}/10")
    
    return {
        "total_queries": total_queries,
        "successful_queries": successful_queries,
        "success_rate": successful_queries/total_queries,
        "avg_response_time": total_response_time/total_queries,
        "avg_quality_score": total_quality_score/successful_queries
    }

def main():
    """Run all persona tests"""
    print("Starting Persona Testing...")
    print(f"Testing {len(PERSONAS)} personas")
    print(f"Total queries: {sum(len(p['queries']) for p in PERSONAS.values())}")
    
    all_results = []
    
    for persona_id, persona_data in PERSONAS.items():
        results = test_persona(persona_id, persona_data)
        all_results.append(results)
        
        # Save individual results
        with open(f"/home/ubuntu/mandate_wizard_web_app/test_results_{persona_id}.json", 'w') as f:
            json.dump(results, f, indent=2)
    
    # Generate summary
    summary = generate_summary(all_results)
    
    # Save summary
    with open("/home/ubuntu/mandate_wizard_web_app/test_summary.json", 'w') as f:
        json.dump({
            "summary": summary,
            "all_results": all_results
        }, f, indent=2)
    
    print(f"\n\nResults saved to test_results_*.json and test_summary.json")

if __name__ == "__main__":
    main()


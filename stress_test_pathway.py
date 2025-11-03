#!/usr/bin/env python3
"""
Comprehensive Stress Test for Mandate Wizard Pathway System
Tests edge cases, failure modes, and quality issues
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class PathwayStressTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.results = []
        self.issues = []
        self.session_id = f"stress_test_{int(time.time())}"
        
    def test_query(self, question: str, expected_executive: str = None, test_name: str = "") -> Dict[str, Any]:
        """Run a single test query and analyze results"""
        print(f"\n{'='*80}")
        print(f"TEST: {test_name}")
        print(f"QUERY: {question}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/ask_pathway",
                json={"question": question, "user_id": self.session_id},
                timeout=180
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code != 200:
                issue = f"❌ HTTP {response.status_code}: {response.text}"
                print(issue)
                self.issues.append({"test": test_name, "issue": issue})
                return {"success": False, "error": issue}
            
            data = response.json()
            
            if not data.get('success', False):
                issue = f"❌ API Error: {data.get('error', 'Unknown error')}"
                print(issue)
                self.issues.append({"test": test_name, "issue": issue})
                return data
            
            # Analyze response quality
            self._analyze_response(data, expected_executive, test_name, elapsed)
            
            return data
            
        except requests.exceptions.Timeout:
            issue = f"❌ TIMEOUT after 180s"
            print(issue)
            self.issues.append({"test": test_name, "issue": issue})
            return {"success": False, "error": "timeout"}
        except Exception as e:
            issue = f"❌ EXCEPTION: {str(e)}"
            print(issue)
            self.issues.append({"test": test_name, "issue": issue})
            return {"success": False, "error": str(e)}
    
    def _analyze_response(self, data: Dict, expected_executive: str, test_name: str, elapsed: float):
        """Critically analyze response quality"""
        issues = []
        
        # 1. Performance check
        print(f"\n⏱️  Response Time: {elapsed:.2f}s")
        if elapsed > 30:
            issues.append(f"SLOW: {elapsed:.2f}s (target: <30s)")
        if elapsed > 60:
            issues.append(f"VERY SLOW: {elapsed:.2f}s (target: <30s)")
        
        # 2. Executive name accuracy
        executive = data.get('executive_name', 'Unknown')
        print(f"👤 Executive: {executive}")
        if expected_executive and executive != expected_executive:
            issues.append(f"WRONG EXECUTIVE: Got '{executive}', expected '{expected_executive}'")
        if executive == "Unknown":
            issues.append("FAILED TO EXTRACT EXECUTIVE NAME")
        
        # 3. Answer quality checks
        answer = data.get('answer', '')
        print(f"📝 Answer Length: {len(answer)} chars")
        
        if len(answer) < 100:
            issues.append(f"TOO SHORT: {len(answer)} chars (target: >200)")
        if len(answer) > 2000:
            issues.append(f"TOO LONG: {len(answer)} chars (target: <1500)")
        
        # Check for hallucinations (common false names)
        hallucination_markers = [
            "I don't know", "I'm not sure", "I cannot", 
            "no information", "not available", "unclear"
        ]
        if any(marker.lower() in answer.lower() for marker in hallucination_markers):
            issues.append("UNCERTAINTY IN ANSWER - may indicate hallucination")
        
        # Check for generic/unhelpful responses
        if "contact Netflix" in answer and executive == "Unknown":
            issues.append("GENERIC ANSWER - didn't identify specific executive")
        
        # 4. Persona detection
        persona = data.get('user_profile', {}).get('persona', 'unknown')
        sophistication = data.get('user_profile', {}).get('sophistication_level', 'unknown')
        print(f"🎭 Persona: {persona} ({sophistication})")
        
        if persona == "unknown":
            issues.append("FAILED TO DETECT PERSONA")
        
        # 5. Follow-ups quality
        followups = data.get('follow_ups', [])
        print(f"❓ Follow-ups: {len(followups)}")
        
        if len(followups) == 0:
            issues.append("NO FOLLOW-UPS GENERATED")
        if len(followups) < 2:
            issues.append(f"TOO FEW FOLLOW-UPS: {len(followups)} (target: 3-5)")
        
        # Check for generic follow-ups
        generic_followups = [
            "Tell me more",
            "What else",
            "Can you explain"
        ]
        if any(any(generic in fu for generic in generic_followups) for fu in followups):
            issues.append("GENERIC FOLLOW-UPS - not contextual")
        
        # 6. Confidence score
        confidence = data.get('confidence_score', 0)
        print(f"🎯 Confidence: {confidence}")
        
        if confidence < 0.5:
            issues.append(f"LOW CONFIDENCE: {confidence} (target: >0.7)")
        
        # 7. Sources
        sources = data.get('sources', [])
        print(f"📚 Sources: {len(sources)}")
        
        if len(sources) == 0:
            issues.append("NO SOURCES PROVIDED")
        
        # Print answer preview
        print(f"\n📄 Answer Preview:")
        print(answer[:300] + "..." if len(answer) > 300 else answer)
        
        # Print follow-ups
        if followups:
            print(f"\n💡 Follow-ups:")
            for i, fu in enumerate(followups, 1):
                print(f"  {i}. {fu}")
        
        # Report issues
        if issues:
            print(f"\n⚠️  ISSUES FOUND ({len(issues)}):")
            for issue in issues:
                print(f"  - {issue}")
            self.issues.extend([{"test": test_name, "issue": issue} for issue in issues])
        else:
            print(f"\n✅ NO ISSUES - PERFECT RESPONSE")
        
        # Store result
        self.results.append({
            "test": test_name,
            "elapsed": elapsed,
            "executive": executive,
            "persona": persona,
            "sophistication": sophistication,
            "confidence": confidence,
            "answer_length": len(answer),
            "followups_count": len(followups),
            "sources_count": len(sources),
            "issues_count": len(issues)
        })
    
    def run_comprehensive_test(self):
        """Run comprehensive test suite"""
        print("\n" + "="*80)
        print("MANDATE WIZARD PATHWAY SYSTEM - COMPREHENSIVE STRESS TEST")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Session ID: {self.session_id}")
        
        # Test 1: Basic routing
        self.test_query(
            "Who handles Korean content?",
            expected_executive="Don Kang",
            test_name="1. Basic Routing"
        )
        
        # Test 2: Ambiguous query
        self.test_query(
            "Who should I pitch my thriller to?",
            expected_executive=None,  # Should ask for clarification or give multiple options
            test_name="2. Ambiguous Query (no region specified)"
        )
        
        # Test 3: Very specific query
        self.test_query(
            "What does Don Kang look for in a Korean thriller series?",
            expected_executive="Don Kang",
            test_name="3. Very Specific Query"
        )
        
        # Test 4: Crisis mode (tight deadline)
        self.test_query(
            "I have 48 hours to decide if I should pitch my Korean drama to Netflix. Who handles this and what do they want?",
            expected_executive="Don Kang",
            test_name="4. Crisis Mode (48-hour deadline)"
        )
        
        # Test 5: Novice-level query
        self.test_query(
            "I'm a new screenwriter. How do I get my script to Netflix?",
            expected_executive=None,  # Should provide education, not just executive name
            test_name="5. Novice Query (needs education)"
        )
        
        # Test 6: Advanced query (competitive intelligence)
        self.test_query(
            "What has Don Kang greenlit in the last 6 months?",
            expected_executive="Don Kang",
            test_name="6. Advanced Query (recent greenlights)"
        )
        
        # Test 7: Multi-region query
        self.test_query(
            "Who handles content in Korea and Japan?",
            expected_executive=None,  # Should mention multiple executives
            test_name="7. Multi-Region Query"
        )
        
        # Test 8: Genre-specific query
        self.test_query(
            "Who at Netflix is looking for true crime documentaries?",
            expected_executive=None,  # Should identify documentary executive
            test_name="8. Genre-Specific Query (documentaries)"
        )
        
        # Test 9: Production company query
        self.test_query(
            "What production companies work with Don Kang?",
            expected_executive="Don Kang",
            test_name="9. Production Company Query"
        )
        
        # Test 10: Pitch process query
        self.test_query(
            "What's the pitch process for Korean content at Netflix?",
            expected_executive="Don Kang",
            test_name="10. Pitch Process Query"
        )
        
        # Test 11: Edge case - misspelled name
        self.test_query(
            "Who is Dong Kang?",
            expected_executive="Don Kang",  # Should handle typo
            test_name="11. Edge Case (misspelled name)"
        )
        
        # Test 12: Edge case - very short query
        self.test_query(
            "Korea?",
            expected_executive="Don Kang",
            test_name="12. Edge Case (one-word query)"
        )
        
        # Test 13: Edge case - very long query
        long_query = "I'm a producer with 15 years of experience in Korean television, and I've developed a thriller series that combines elements of Squid Game's social commentary with the psychological depth of Hellbound, and I'm wondering who at Netflix would be the right person to pitch this to, and what specific elements they're looking for in Korean thriller content right now, and whether there's a specific format or approach that works best for pitching to them?"
        self.test_query(
            long_query,
            expected_executive="Don Kang",
            test_name="13. Edge Case (very long query)"
        )
        
        # Test 14: Follow-up question (tests memory)
        self.test_query(
            "What else does he look for?",
            expected_executive="Don Kang",  # Should remember context
            test_name="14. Follow-up (tests memory)"
        )
        
        # Test 15: Comparative query
        self.test_query(
            "How does Don Kang's mandate differ from other regional executives?",
            expected_executive="Don Kang",
            test_name="15. Comparative Query"
        )
        
        # Test 16: Timing query
        self.test_query(
            "When is the best time to pitch to Don Kang?",
            expected_executive="Don Kang",
            test_name="16. Timing/Strategy Query"
        )
        
        # Test 17: Budget query
        self.test_query(
            "What's the typical budget range for Korean series at Netflix?",
            expected_executive="Don Kang",
            test_name="17. Budget/Financial Query"
        )
        
        # Test 18: Competitive query
        self.test_query(
            "What Korean content is Netflix developing right now?",
            expected_executive="Don Kang",
            test_name="18. Competitive Intelligence Query"
        )
        
        # Test 19: Relationship query
        self.test_query(
            "Who does Don Kang report to?",
            expected_executive="Don Kang",
            test_name="19. Organizational Structure Query"
        )
        
        # Test 20: Strategic query
        self.test_query(
            "What's Netflix's overall strategy for Korean content in 2025?",
            expected_executive="Don Kang",
            test_name="20. Strategic Overview Query"
        )
        
        # Generate final report
        self._generate_report()
    
    def _generate_report(self):
        """Generate comprehensive test report"""
        print("\n\n" + "="*80)
        print("FINAL TEST REPORT")
        print("="*80)
        
        # Summary statistics
        total_tests = len(self.results)
        total_issues = len(self.issues)
        avg_time = sum(r['elapsed'] for r in self.results) / total_tests if total_tests > 0 else 0
        avg_confidence = sum(r['confidence'] for r in self.results) / total_tests if total_tests > 0 else 0
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Total Issues: {total_issues}")
        print(f"  Average Response Time: {avg_time:.2f}s")
        print(f"  Average Confidence: {avg_confidence:.2f}")
        
        # Performance breakdown
        print(f"\n⏱️  PERFORMANCE:")
        fast = sum(1 for r in self.results if r['elapsed'] < 15)
        medium = sum(1 for r in self.results if 15 <= r['elapsed'] < 30)
        slow = sum(1 for r in self.results if r['elapsed'] >= 30)
        print(f"  Fast (<15s): {fast}")
        print(f"  Medium (15-30s): {medium}")
        print(f"  Slow (>30s): {slow}")
        
        # Quality breakdown
        print(f"\n🎯 QUALITY:")
        perfect = sum(1 for r in self.results if r['issues_count'] == 0)
        minor = sum(1 for r in self.results if 1 <= r['issues_count'] <= 2)
        major = sum(1 for r in self.results if r['issues_count'] > 2)
        print(f"  Perfect (0 issues): {perfect}")
        print(f"  Minor issues (1-2): {minor}")
        print(f"  Major issues (3+): {major}")
        
        # Issue breakdown by category
        print(f"\n⚠️  ISSUES BY CATEGORY:")
        issue_categories = {}
        for issue in self.issues:
            category = issue['issue'].split(':')[0]
            issue_categories[category] = issue_categories.get(category, 0) + 1
        
        for category, count in sorted(issue_categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: {count}")
        
        # Critical issues
        critical_issues = [i for i in self.issues if any(word in i['issue'] for word in ['FAILED', 'WRONG', 'TIMEOUT', 'ERROR'])]
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES ({len(critical_issues)}):")
            for issue in critical_issues[:10]:  # Show top 10
                print(f"  - [{issue['test']}] {issue['issue']}")
        
        # Save detailed results
        output_file = f"/home/ubuntu/mandate_wizard_web_app/stress_test_results_{self.session_id}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "total_issues": total_issues,
                    "avg_time": avg_time,
                    "avg_confidence": avg_confidence
                },
                "results": self.results,
                "issues": self.issues
            }, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
        # Final grade
        success_rate = (perfect / total_tests * 100) if total_tests > 0 else 0
        print(f"\n🎓 FINAL GRADE:")
        if success_rate >= 90:
            grade = "A (Excellent)"
        elif success_rate >= 75:
            grade = "B (Good)"
        elif success_rate >= 60:
            grade = "C (Acceptable)"
        elif success_rate >= 50:
            grade = "D (Needs Improvement)"
        else:
            grade = "F (Major Issues)"
        
        print(f"  Success Rate: {success_rate:.1f}%")
        print(f"  Grade: {grade}")
        
        print("\n" + "="*80)
        print("TEST COMPLETE")
        print("="*80)

if __name__ == '__main__':
    tester = PathwayStressTester()
    tester.run_comprehensive_test()


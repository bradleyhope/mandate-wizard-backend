#!/usr/bin/env python3
"""
Comprehensive Platform Coverage Audit
Analyzes database to identify platform coverage, data completeness, and gaps
"""

import requests
import json
from collections import defaultdict, Counter
from typing import Dict, List

BACKEND_URL = "http://localhost:5000"

def fetch_all_data():
    """Fetch all data from backend APIs"""
    print("Fetching data from backend APIs...")
    
    data = {
        "greenlights": [],
        "quotes": [],
        "deals": []
    }
    
    try:
        # Fetch greenlights
        response = requests.get(f"{BACKEND_URL}/api/recent-mandates/greenlights", timeout=30)
        if response.status_code == 200:
            result = response.json()
            data["greenlights"] = result.get("greenlights", [])
            print(f"✓ Fetched {len(data['greenlights'])} greenlights")
        
        # Fetch quotes
        response = requests.get(f"{BACKEND_URL}/api/recent-mandates/quotes", timeout=30)
        if response.status_code == 200:
            result = response.json()
            data["quotes"] = result.get("quotes", [])
            print(f"✓ Fetched {len(data['quotes'])} quotes")
        
        # Fetch deals
        response = requests.get(f"{BACKEND_URL}/api/recent-mandates/deals", timeout=30)
        if response.status_code == 200:
            result = response.json()
            data["deals"] = result.get("deals", [])
            print(f"✓ Fetched {len(data['deals'])} deals")
            
    except Exception as e:
        print(f"Error fetching data: {e}")
    
    return data

def analyze_platform_coverage(data: Dict) -> Dict:
    """Analyze platform/streamer coverage"""
    print("\n" + "="*80)
    print("PLATFORM COVERAGE ANALYSIS")
    print("="*80)
    
    # Analyze greenlights by platform
    greenlight_platforms = Counter()
    for g in data["greenlights"]:
        platform = g.get("streamer", "Unknown")
        if platform and platform.strip():
            greenlight_platforms[platform] += 1
        else:
            greenlight_platforms["Unknown"] += 1
    
    print(f"\n📺 GREENLIGHTS BY PLATFORM ({len(data['greenlights'])} total)")
    print("-" * 80)
    for platform, count in greenlight_platforms.most_common():
        percentage = (count / len(data["greenlights"]) * 100) if data["greenlights"] else 0
        print(f"  {platform:30s} {count:3d} greenlights ({percentage:5.1f}%)")
    
    # Analyze deals by platform
    deal_platforms = Counter()
    for d in data["deals"]:
        platform = d.get("streamer", "Unknown")
        if platform and platform.strip():
            deal_platforms[platform] += 1
        else:
            deal_platforms["Unknown"] += 1
    
    print(f"\n🤝 PRODUCTION DEALS BY PLATFORM ({len(data['deals'])} total)")
    print("-" * 80)
    for platform, count in deal_platforms.most_common():
        percentage = (count / len(data["deals"]) * 100) if data["deals"] else 0
        print(f"  {platform:30s} {count:3d} deals ({percentage:5.1f}%)")
    
    # Analyze quotes by context (may contain platform mentions)
    print(f"\n💬 QUOTES ({len(data['quotes'])} total)")
    print("-" * 80)
    quote_contexts = []
    for q in data["quotes"]:
        context = q.get("context", "")
        if context:
            quote_contexts.append(context)
    print(f"  {len(quote_contexts)} quotes have context")
    print(f"  {len(data['quotes']) - len(quote_contexts)} quotes missing context")
    
    return {
        "greenlight_platforms": dict(greenlight_platforms),
        "deal_platforms": dict(deal_platforms),
        "total_platforms": len(set(list(greenlight_platforms.keys()) + list(deal_platforms.keys())))
    }

def analyze_data_completeness(data: Dict) -> Dict:
    """Analyze data completeness for each entity type"""
    print("\n" + "="*80)
    print("DATA COMPLETENESS ANALYSIS")
    print("="*80)
    
    # Greenlight completeness
    print(f"\n🎬 GREENLIGHT DATA COMPLETENESS ({len(data['greenlights'])} total)")
    print("-" * 80)
    
    greenlight_fields = {
        "title": 0,
        "streamer": 0,
        "genre": 0,
        "format": 0,
        "year": 0,
        "date": 0,
        "description": 0,
        "executive": 0,
        "production_company": 0,
        "talent": 0
    }
    
    for g in data["greenlights"]:
        for field in greenlight_fields:
            value = g.get(field, "")
            if value and str(value).strip() and str(value).lower() not in ["unknown", "none", "null"]:
                greenlight_fields[field] += 1
    
    for field, count in sorted(greenlight_fields.items(), key=lambda x: -x[1]):
        percentage = (count / len(data["greenlights"]) * 100) if data["greenlights"] else 0
        status = "✓" if percentage >= 80 else "⚠" if percentage >= 50 else "✗"
        print(f"  {status} {field:20s} {count:3d}/{len(data['greenlights']):3d} ({percentage:5.1f}%)")
    
    # Deal completeness
    print(f"\n🤝 PRODUCTION DEAL DATA COMPLETENESS ({len(data['deals'])} total)")
    print("-" * 80)
    
    deal_fields = {
        "company": 0,
        "streamer": 0,
        "deal_type": 0,
        "year": 0,
        "genre": 0,
        "notable_projects": 0,
        "executives": 0
    }
    
    for d in data["deals"]:
        for field in deal_fields:
            value = d.get(field, "")
            if value and str(value).strip() and str(value).lower() not in ["unknown", "none", "null"]:
                deal_fields[field] += 1
    
    for field, count in sorted(deal_fields.items(), key=lambda x: -x[1]):
        percentage = (count / len(data["deals"]) * 100) if data["deals"] else 0
        status = "✓" if percentage >= 80 else "⚠" if percentage >= 50 else "✗"
        print(f"  {status} {field:20s} {count:3d}/{len(data['deals']):3d} ({percentage:5.1f}%)")
    
    # Quote completeness
    print(f"\n💬 QUOTE DATA COMPLETENESS ({len(data['quotes'])} total)")
    print("-" * 80)
    
    quote_fields = {
        "executive": 0,
        "quote_text": 0,
        "context": 0,
        "date": 0,
        "source": 0
    }
    
    for q in data["quotes"]:
        for field in quote_fields:
            value = q.get(field, "")
            if value and str(value).strip() and str(value).lower() not in ["unknown", "none", "null"]:
                quote_fields[field] += 1
    
    for field, count in sorted(quote_fields.items(), key=lambda x: -x[1]):
        percentage = (count / len(data["quotes"]) * 100) if data["quotes"] else 0
        status = "✓" if percentage >= 80 else "⚠" if percentage >= 50 else "✗"
        print(f"  {status} {field:20s} {count:3d}/{len(data['quotes']):3d} ({percentage:5.1f}%)")
    
    return {
        "greenlight_completeness": greenlight_fields,
        "deal_completeness": deal_fields,
        "quote_completeness": quote_fields
    }

def identify_critical_gaps(coverage: Dict, completeness: Dict) -> List[str]:
    """Identify critical gaps that need immediate attention"""
    print("\n" + "="*80)
    print("CRITICAL GAPS IDENTIFIED")
    print("="*80)
    
    gaps = []
    
    # Platform diversity gap
    if coverage["total_platforms"] <= 2:
        gap = f"⚠️  CRITICAL: Only {coverage['total_platforms']} platform(s) covered - need Amazon, Apple TV+, Disney+, HBO Max, etc."
        print(f"\n{gap}")
        gaps.append(gap)
    
    # Executive relationship gap
    exec_coverage = completeness["greenlight_completeness"].get("executive", 0)
    total_greenlights = len(completeness["greenlight_completeness"])
    if total_greenlights > 0:
        exec_percentage = (exec_coverage / total_greenlights * 100)
        if exec_percentage < 50:
            gap = f"⚠️  HIGH: Only {exec_percentage:.1f}% of greenlights have executive attribution"
            print(f"\n{gap}")
            gaps.append(gap)
    
    # Production company gap
    prod_coverage = completeness["greenlight_completeness"].get("production_company", 0)
    if total_greenlights > 0:
        prod_percentage = (prod_coverage / total_greenlights * 100)
        if prod_percentage < 50:
            gap = f"⚠️  HIGH: Only {prod_percentage:.1f}% of greenlights have production company attribution"
            print(f"\n{gap}")
            gaps.append(gap)
    
    # Talent gap
    talent_coverage = completeness["greenlight_completeness"].get("talent", 0)
    if total_greenlights > 0:
        talent_percentage = (talent_coverage / total_greenlights * 100)
        if talent_percentage < 30:
            gap = f"⚠️  MEDIUM: Only {talent_percentage:.1f}% of greenlights have talent attribution (showrunners, actors, directors)"
            print(f"\n{gap}")
            gaps.append(gap)
    
    # Description/logline gap
    desc_coverage = completeness["greenlight_completeness"].get("description", 0)
    if total_greenlights > 0:
        desc_percentage = (desc_coverage / total_greenlights * 100)
        if desc_percentage < 70:
            gap = f"⚠️  MEDIUM: Only {desc_percentage:.1f}% of greenlights have descriptions/loglines"
            print(f"\n{gap}")
            gaps.append(gap)
    
    if not gaps:
        print("\n✓ No critical gaps identified - database quality is good!")
    
    return gaps

def generate_recommendations(gaps: List[str], coverage: Dict) -> List[str]:
    """Generate actionable recommendations"""
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)
    
    recommendations = []
    
    # Platform expansion
    if coverage["total_platforms"] <= 2:
        rec = """
1. IMMEDIATE: Multi-Platform Expansion
   - Add Amazon Prime Video greenlights and deals
   - Add Apple TV+ greenlights and deals
   - Add Disney+ greenlights and deals
   - Add HBO Max greenlights and deals
   - Add broadcast networks (ABC, NBC, CBS, Fox)
   - Add cable networks (FX, AMC, Showtime)
   - Priority: Start with streaming platforms (highest user interest)
        """
        print(rec)
        recommendations.append(rec)
    
    # Executive expansion
    rec = """
2. HIGH PRIORITY: Executive Relationship Mapping
   - Map executives to greenlights using Deadline, Variety, THR articles
   - Create executive profiles with titles and responsibilities
   - Build executive-greenlight relationships in Neo4j
   - Target: 150+ executives across all platforms
    """
    print(rec)
    recommendations.append(rec)
    
    # Production company expansion
    rec = """
3. HIGH PRIORITY: Production Company Attribution
   - Identify production companies for each greenlight
   - Create production company nodes in Neo4j
   - Map company-greenlight relationships
   - Include company-executive relationships
    """
    print(rec)
    recommendations.append(rec)
    
    # Talent attribution
    rec = """
4. MEDIUM PRIORITY: Talent Attribution
   - Add showrunners to series greenlights
   - Add directors to limited series and films
   - Add lead actors/actresses
   - Create talent nodes and relationships in Neo4j
    """
    print(rec)
    recommendations.append(rec)
    
    # Historical data
    rec = """
5. MEDIUM PRIORITY: Historical Data Ingestion
   - Backfill 2022-2024 greenlights for pattern analysis
   - Focus on successful shows that got renewed
   - Include cancellation data for risk analysis
    """
    print(rec)
    recommendations.append(rec)
    
    return recommendations

def main():
    """Run comprehensive platform coverage audit"""
    print("\n" + "="*80)
    print("MANDATE WIZARD - COMPREHENSIVE PLATFORM COVERAGE AUDIT")
    print("="*80)
    
    # Fetch all data
    data = fetch_all_data()
    
    # Analyze platform coverage
    coverage = analyze_platform_coverage(data)
    
    # Analyze data completeness
    completeness = analyze_data_completeness(data)
    
    # Identify critical gaps
    gaps = identify_critical_gaps(coverage, completeness)
    
    # Generate recommendations
    recommendations = generate_recommendations(gaps, coverage)
    
    # Save detailed report
    report = {
        "summary": {
            "total_greenlights": len(data["greenlights"]),
            "total_quotes": len(data["quotes"]),
            "total_deals": len(data["deals"]),
            "platforms_covered": coverage["total_platforms"],
            "critical_gaps": len(gaps)
        },
        "platform_coverage": coverage,
        "data_completeness": completeness,
        "critical_gaps": gaps,
        "recommendations": recommendations
    }
    
    output_file = "/home/ubuntu/platform_coverage_audit.json"
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n" + "="*80)
    print(f"✓ Detailed report saved to: {output_file}")
    print("="*80)

if __name__ == "__main__":
    main()

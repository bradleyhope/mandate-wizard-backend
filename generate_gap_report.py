#!/usr/bin/env python3
"""
Generate Comprehensive Gap Report
Analyzes all healed records to identify missing entities
"""

import json
import glob
from collections import defaultdict

print("=" * 70)
print("📊 COMPREHENSIVE GAP ANALYSIS")
print("=" * 70)

# Load all checkpoint files
checkpoint_files = glob.glob("/home/ubuntu/mandate_wizard_web_app/checkpoint_worker_*.json")
print(f"\nAnalyzing {len(checkpoint_files)} checkpoint files...")

# Aggregate all gaps
all_missing_people = defaultdict(lambda: {"count": 0, "importance": "low", "contexts": []})
all_missing_companies = defaultdict(lambda: {"count": 0, "importance": "low", "contexts": []})
all_missing_projects = defaultdict(lambda: {"count": 0, "contexts": []})

total_records = 0

for checkpoint_file in sorted(checkpoint_files):
    with open(checkpoint_file, 'r') as f:
        data = json.load(f)
    
    healed_records = data.get("healed_records", [])
    total_records += len(healed_records)
    
    for record in healed_records:
        gaps = record.get("gaps", {})
        
        # Missing people
        for person in gaps.get("missing_people", []):
            name = person.get("name", "Unknown")
            all_missing_people[name]["count"] += 1
            all_missing_people[name]["importance"] = person.get("importance", "low")
            all_missing_people[name]["contexts"].append(record["name"])
        
        # Missing companies
        for company in gaps.get("missing_companies", []):
            name = company.get("name", "Unknown")
            all_missing_companies[name]["count"] += 1
            all_missing_companies[name]["importance"] = company.get("importance", "low")
            all_missing_companies[name]["contexts"].append(record["name"])
        
        # Missing projects
        for project in gaps.get("missing_projects", []):
            all_missing_projects[project]["count"] += 1
            all_missing_projects[project]["contexts"].append(record["name"])

print(f"Analyzed {total_records} healed records\n")

# Sort by importance and frequency
def sort_key(item):
    name, data = item
    importance_score = {"high": 3, "medium": 2, "low": 1}.get(data["importance"], 0)
    return (importance_score, data["count"])

sorted_people = sorted(all_missing_people.items(), key=sort_key, reverse=True)
sorted_companies = sorted(all_missing_companies.items(), key=sort_key, reverse=True)
sorted_projects = sorted(all_missing_projects.items(), key=lambda x: x[1]["count"], reverse=True)

# Generate report
print("=" * 70)
print("🔍 MISSING PEOPLE")
print("=" * 70)
print(f"Total unique people: {len(sorted_people)}\n")

print("Top 50 High-Priority People:")
high_priority = [(name, data) for name, data in sorted_people if data["importance"] == "high"][:50]
for i, (name, data) in enumerate(high_priority, 1):
    print(f"{i:2}. {name:40} (mentioned {data['count']}x)")

print("\n" + "=" * 70)
print("🏢 MISSING PRODUCTION COMPANIES")
print("=" * 70)
print(f"Total unique companies: {len(sorted_companies)}\n")

print("Top 30 High-Priority Companies:")
high_priority_companies = [(name, data) for name, data in sorted_companies if data["importance"] == "high"][:30]
for i, (name, data) in enumerate(high_priority_companies, 1):
    print(f"{i:2}. {name:40} (mentioned {data['count']}x)")

print("\n" + "=" * 70)
print("🎬 MISSING PROJECTS")
print("=" * 70)
print(f"Total unique projects: {len(sorted_projects)}\n")

print("Top 20 Most Mentioned Projects:")
for i, (name, data) in enumerate(sorted_projects[:20], 1):
    print(f"{i:2}. {name:40} (mentioned {data['count']}x)")

# Save detailed report
report = {
    "summary": {
        "total_records_analyzed": total_records,
        "total_missing_people": len(all_missing_people),
        "total_missing_companies": len(all_missing_companies),
        "total_missing_projects": len(all_missing_projects),
        "high_priority_people": len([p for p, d in sorted_people if d["importance"] == "high"]),
        "high_priority_companies": len([c for c, d in sorted_companies if d["importance"] == "high"])
    },
    "missing_people": {
        name: {
            "mentions": data["count"],
            "importance": data["importance"],
            "sample_contexts": data["contexts"][:3]
        }
        for name, data in sorted_people
    },
    "missing_companies": {
        name: {
            "mentions": data["count"],
            "importance": data["importance"],
            "sample_contexts": data["contexts"][:3]
        }
        for name, data in sorted_companies
    },
    "missing_projects": {
        name: {
            "mentions": data["count"],
            "sample_contexts": data["contexts"][:3]
        }
        for name, data in sorted_projects
    }
}

with open("/home/ubuntu/comprehensive_gap_report.json", "w") as f:
    json.dump(report, f, indent=2)

print("\n" + "=" * 70)
print("📄 REPORT SAVED")
print("=" * 70)
print("Detailed report: /home/ubuntu/comprehensive_gap_report.json")
print("\n✅ Gap analysis complete!")


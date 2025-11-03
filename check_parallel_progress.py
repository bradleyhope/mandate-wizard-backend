#!/usr/bin/env python3
"""
Check progress of parallel healing workers
"""

import json
import os
import glob
from datetime import datetime

print("=" * 70)
print("📊 PARALLEL HEALING PROGRESS REPORT")
print("=" * 70)
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Find all checkpoint files
checkpoint_files = glob.glob("/home/ubuntu/mandate_wizard_web_app/checkpoint_worker_*.json")

if not checkpoint_files:
    print("❌ No checkpoint files found yet. Workers may still be starting up.")
    exit(0)

total_healed = 0
total_expected = 0
workers_data = []

for checkpoint_file in sorted(checkpoint_files):
    try:
        with open(checkpoint_file, 'r') as f:
            data = json.load(f)
        
        worker_id = data["worker_id"]
        start = data["start_index"]
        end = data["end_index"]
        current = data["current_index"]
        healed = data["healed_count"]
        expected = end - start + 1
        progress = (current - start + 1) / expected * 100
        
        workers_data.append({
            "id": worker_id,
            "start": start,
            "end": end,
            "current": current,
            "healed": healed,
            "expected": expected,
            "progress": progress,
            "final": data.get("final", False)
        })
        
        total_healed += healed
        total_expected += expected
        
    except Exception as e:
        print(f"⚠️  Error reading {checkpoint_file}: {e}")

# Sort by worker ID
workers_data.sort(key=lambda x: x["id"])

# Display worker status
for w in workers_data:
    status = "✅ COMPLETE" if w["final"] else "🔄 RUNNING"
    print(f"Worker {w['id']}: {status}")
    print(f"  Range: {w['start']}-{w['end']} ({w['expected']} mandates)")
    print(f"  Progress: {w['current']}/{w['end']} ({w['progress']:.1f}%)")
    print(f"  Healed: {w['healed']}")
    print()

# Overall progress
overall_progress = (total_healed / total_expected * 100) if total_expected > 0 else 0

print("=" * 70)
print("OVERALL PROGRESS")
print("=" * 70)
print(f"Total Healed: {total_healed}/{total_expected} ({overall_progress:.1f}%)")
print(f"Workers Complete: {sum(1 for w in workers_data if w['final'])}/{len(workers_data)}")

# Estimate completion
if total_healed > 0 and not all(w["final"] for w in workers_data):
    # Find average rate
    rates = []
    for w in workers_data:
        if not w["final"] and w["healed"] > 0:
            # Rough estimate: assume linear progress
            rates.append(w["healed"] / (w["current"] - w["start"] + 1))
    
    if rates:
        avg_rate = sum(rates) / len(rates)
        remaining = total_expected - total_healed
        est_time_mins = remaining / avg_rate * 2  # 2 minutes per mandate
        est_hours = est_time_mins / 60
        print(f"\nEstimated time remaining: ~{est_hours:.1f} hours")

print("=" * 70)


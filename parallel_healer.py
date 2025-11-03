#!/usr/bin/env python3
"""
Parallel Database Healer - Launches multiple healing workers
Processes mandates in parallel to speed up healing by 3-5x
"""

import subprocess
import time
import sys

# Configuration
NUM_WORKERS = 5
START_INDEX = 103  # Resume from where we left off
TOTAL_MANDATES = 825
REMAINING = TOTAL_MANDATES - START_INDEX + 1  # 723 mandates

# Calculate batch sizes
batch_size = REMAINING // NUM_WORKERS
batches = []

for i in range(NUM_WORKERS):
    start = START_INDEX + (i * batch_size)
    if i == NUM_WORKERS - 1:
        # Last batch gets any remainder
        end = TOTAL_MANDATES
    else:
        end = start + batch_size - 1
    batches.append((start, end, end - start + 1))

print("=" * 70)
print("🚀 PARALLEL DATABASE HEALER")
print("=" * 70)
print(f"\nConfiguration:")
print(f"  Workers: {NUM_WORKERS}")
print(f"  Total mandates to process: {REMAINING}")
print(f"  Batch size: ~{batch_size} per worker")
print(f"\nBatch assignments:")

for i, (start, end, count) in enumerate(batches, 1):
    print(f"  Worker {i}: Mandates {start}-{end} ({count} total)")

print(f"\n{'='*70}")
print("Starting workers...")
print("=" * 70)

# Launch workers
processes = []
for i, (start, end, count) in enumerate(batches, 1):
    log_file = f"healer_worker_{i}.log"
    
    cmd = [
        "python3", "-u", "intelligent_healer_v2_worker.py",
        str(start), str(end), str(i)
    ]
    
    with open(log_file, 'w') as f:
        proc = subprocess.Popen(
            cmd,
            stdout=f,
            stderr=subprocess.STDOUT,
            cwd="/home/ubuntu/mandate_wizard_web_app"
        )
    
    processes.append((i, proc, log_file, start, end, count))
    print(f"✅ Worker {i} started (PID: {proc.pid}) -> {log_file}")
    time.sleep(1)  # Stagger starts slightly

print(f"\n{'='*70}")
print("All workers launched!")
print("=" * 70)
print("\nMonitor progress with:")
for i, _, log_file, _, _, _ in processes:
    print(f"  tail -f {log_file}")

print("\nCheck overall progress:")
print("  python3 check_parallel_progress.py")

print("\n" + "=" * 70)
print("Workers running in background. This script will now exit.")
print("Workers will continue running independently.")
print("=" * 70)


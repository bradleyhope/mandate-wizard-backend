"""
MEMORY-OPTIMIZED Gunicorn Configuration for Mandate Wizard
Designed for Railway/Render deployment with 512MB-2GB RAM limits
"""

import os

# Server socket
port = os.environ.get('PORT', '5000')
bind = f"0.0.0.0:{port}"
backlog = 2048

# ⚡ CRITICAL MEMORY OPTIMIZATION: Single worker only
# Multiple workers = multiple copies of ML models in memory
workers = 1  # MUST be 1 to fit in 512MB-1GB RAM

# Use gevent for async I/O (handles multiple requests with single worker)
worker_class = "gevent"
worker_connections = 100  # Reduced from 1000 to save memory

# Timeouts
timeout = 120  # Allow time for OpenAI API calls
keepalive = 5

# ⚡ MEMORY OPTIMIZATION: Restart worker periodically to prevent leaks
max_requests = 100  # Restart after 100 requests (was 1000)
max_requests_jitter = 10

# ⚡ CRITICAL: Do NOT preload app (saves memory)
preload_app = False

# Logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"

# Process naming
proc_name = "mandate_wizard_optimized"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# ⚡ MEMORY LIMIT: Set worker memory limit (Railway/Render will kill if exceeded)
# This is a soft limit - worker will restart before hitting hard limit
limit_request_line = 4096  # Limit request header size
limit_request_fields = 100
limit_request_field_size = 8190

# Worker lifecycle hooks for memory monitoring
def on_starting(server):
    """Called just before the master process is initialized"""
    print("="*80)
    print("🚀 MEMORY-OPTIMIZED MANDATE WIZARD STARTING")
    print("="*80)
    print(f"Workers: {workers} (single worker for memory optimization)")
    print(f"Worker class: {worker_class}")
    print(f"Max requests per worker: {max_requests}")
    print(f"Preload app: {preload_app} (disabled to save memory)")
    print("="*80)

def worker_int(worker):
    """Called when worker receives INT or QUIT signal"""
    print(f"⚠️  Worker {worker.pid} interrupted - cleaning up...")

def post_worker_init(worker):
    """Called after worker process has been initialized"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    print(f"✓ Worker {worker.pid} initialized - Memory: {memory_mb:.1f} MB")
    
    # Warn if memory usage is high
    if memory_mb > 400:
        print(f"⚠️  WARNING: Worker memory usage is high ({memory_mb:.1f} MB)")
        print("   Consider optimizing or upgrading to a larger instance")

def pre_request(worker, req):
    """Called before processing each request"""
    # Optional: Log memory before each request (can be noisy)
    pass

def post_request(worker, req, environ, resp):
    """Called after processing each request"""
    # Optional: Monitor memory after requests
    # Useful for debugging memory leaks
    pass

def worker_exit(server, worker):
    """Called when worker is about to exit"""
    import psutil
    import os
    
    try:
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"👋 Worker {worker.pid} exiting - Final memory: {memory_mb:.1f} MB")
    except:
        pass

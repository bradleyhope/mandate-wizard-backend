"""
Gunicorn Configuration for Mandate Wizard
Optimized for Railway deployment
"""

import multiprocessing
import os

# Server socket - Use Railway's PORT environment variable
port = os.environ.get('PORT', '5000')
bind = f"0.0.0.0:{port}"
backlog = 2048

# Worker processes - Minimal for cost optimization
workers = 1  # Single worker to minimize memory usage and costs
worker_class = "gevent"  # Async worker for better concurrency
worker_connections = 1000
timeout = 120  # Increased for GPT-5 calls
keepalive = 5

# Logging - Use stdout/stderr for Railway (Railway captures these automatically)
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "mandate_wizard"

# Server mechanics
daemon = False
pidfile = None  # Don't use pidfile on Railway
user = None
group = None
tmp_upload_dir = None

# Performance
preload_app = False  # Disabled to reduce memory usage with ML models
max_requests = 1000  # Restart workers after N requests (prevent memory leaks)
max_requests_jitter = 50  # Add randomness to prevent all workers restarting at once

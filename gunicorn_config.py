"""
Gunicorn Configuration for Mandate Wizard
Optimized for performance and concurrency
"""

import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Recommended formula
worker_class = "gevent"  # Async worker for better concurrency
worker_connections = 1000
timeout = 120  # Increased for GPT-5 calls
keepalive = 5

# Logging
accesslog = "/home/ubuntu/mandate_wizard_web_app/access.log"
errorlog = "/home/ubuntu/mandate_wizard_web_app/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "mandate_wizard"

# Server mechanics
daemon = False
pidfile = "/home/ubuntu/mandate_wizard_web_app/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# Performance
preload_app = True  # Load app before forking workers
max_requests = 1000  # Restart workers after N requests (prevent memory leaks)
max_requests_jitter = 50  # Add randomness to prevent all workers restarting at once

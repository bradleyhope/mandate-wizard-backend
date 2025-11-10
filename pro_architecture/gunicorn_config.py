import os

port = os.environ.get("PORT", "5000")
bind = f"0.0.0.0:{port}"
backlog = 2048

# Keep to 1 worker unless you have >3–4 GB; model residency matters.
workers = int(os.environ.get("WEB_CONCURRENCY", "1"))
worker_class = "sync"
threads = int(os.environ.get("WEB_THREADS", "1"))

timeout = int(os.environ.get("WEB_TIMEOUT", "120"))
keepalive = 2
graceful_timeout = 30

preload_app = False
max_requests = 1000
max_requests_jitter = 50

errorlog = "-"
accesslog = "-"
loglevel = os.environ.get("LOG_LEVEL", "info")

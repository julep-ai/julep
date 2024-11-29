import multiprocessing
import os

debug = os.getenv("AGENTS_API_DEBUG", "false").lower() == "true"

# Gunicorn config variables
workers = (multiprocessing.cpu_count() // 2) if not debug else 1
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8080"
keepalive = 120
timeout = 120
errorlog = "-"
accesslog = "-"

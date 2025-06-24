import os
from agents_api.env import gunicorn_workers

debug = os.getenv("DEBUG", "false").lower() == "true"

# Gunicorn config variables
workers = gunicorn_workers if not debug else 1
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8080"
keepalive = 120
timeout = 120
errorlog = "-"
accesslog = "-"

import multiprocessing
import os

TESTING = os.getenv("TESTING", "false").lower() == "true"
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Gunicorn config variables
workers = multiprocessing.cpu_count() - 1 if not (TESTING or DEBUG) else 1
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
keepalive = 120
timeout = 120
errorlog = "-"
accesslog = "-"
loglevel = "info"
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 50
preload_app = False


def when_ready(server):
    """Run when server is ready to handle requests."""
    # Ensure proper permissions for any required directories
    for directory in ["logs", "run"]:
        path = os.path.join(os.getcwd(), directory)
        if not os.path.exists(path):
            os.makedirs(path, mode=0o755)


def on_starting(server):
    """Run when server starts."""
    server.log.setup(server.app.cfg)


def worker_exit(server, worker):
    """Clean up on worker exit."""
    server.log.info(f"Worker {worker.pid} exiting gracefully")

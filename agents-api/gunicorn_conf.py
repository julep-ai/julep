import multiprocessing

# Gunicorn config variables
workers = multiprocessing.cpu_count() - 1
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8080"
keepalive = 120
timeout = 120
errorlog = "-"
accesslog = "-"

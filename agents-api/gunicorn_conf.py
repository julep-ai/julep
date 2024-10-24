import multiprocessing

# Gunicorn config variables
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8080"
keepalive = 120
errorlog = "-"
accesslog = "-"

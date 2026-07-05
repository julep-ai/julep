FROM python:3.12-slim
# This sandbox egresses through a TLS-intercepting proxy; trust its CA for pip.
COPY ca-bundle.crt /etc/ssl/certs/ca-bundle.crt
ENV PIP_CERT=/etc/ssl/certs/ca-bundle.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt
COPY julep-v2 /src/julep-v2
RUN pip install --no-cache-dir '/src/julep-v2[temporal]'
COPY demo_worker.py /app/demo_worker.py
ENV PYTHONPATH=/app \
    WORKER_CONTEXT_FACTORY=demo_worker:make_context \
    WORKER_HEALTH_PORT=8080
ENTRYPOINT ["julep", "worker"]

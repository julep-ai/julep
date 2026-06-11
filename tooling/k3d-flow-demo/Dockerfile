FROM python:3.12-slim
COPY julep-v2 /src/julep-v2
RUN pip install --no-cache-dir '/src/julep-v2[temporal,http,providers]' 'any-llm-sdk[anthropic]'
COPY episode_summary_flow.py /app/episode_summary_flow.py
COPY flow_worker.py /app/flow_worker.py
ENV PYTHONPATH=/app \
    WORKER_CONTEXT_FACTORY=flow_worker:make_context \
    WORKER_HEALTH_PORT=8080
ENTRYPOINT ["composable-agents", "worker"]

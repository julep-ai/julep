FROM python:3.12-slim
COPY julep-v2 /src/julep-v2
RUN pip install --no-cache-dir '/src/julep-v2[temporal,http,providers]' 'any-llm-sdk[anthropic,openai]'
COPY llm_weather_agent.py /app/llm_weather_agent.py
ENV PYTHONPATH=/app \
    WORKER_CONTEXT_FACTORY=llm_weather_agent:make_context \
    WORKER_HEALTH_PORT=8080
ENTRYPOINT ["julep", "worker"]

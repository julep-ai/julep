FROM python:3.10-slim

ENV PYTHONUNBUFFERED True
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

RUN pip install 'poetry<=1.9.0' \
    && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-dev --no-root

COPY . ./

RUN poetry install --no-dev

ENTRYPOINT ["python", "agents_api/web.py", "--host", "0.0.0.0", "--port", "8080"]

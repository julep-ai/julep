# syntax=docker/dockerfile:1
# check=error=true

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

RUN pip install 'poetry>=1.8.0,<1.9.0' \
    && poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

RUN apt-get update && apt-get install -y --no-install-recommends \
    dpkg-dev \
    gcc \
    g++ \
    libbluetooth-dev \
    libbz2-dev \
    libc6-dev \
    libexpat1-dev \
    libffi-dev \
    libgdbm-dev \
    liblzma-dev \
    libncursesw5-dev \
    libreadline-dev \
    libsqlite3-dev \
    libssl-dev \
    make \
    tk-dev \
    uuid-dev \
    wget \
    xz-utils \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
    
RUN poetry install --no-dev --no-root

COPY . ./

ENTRYPOINT ["python", "-m", "agents_api.web", "--host", "0.0.0.0", "--port", "8080"]

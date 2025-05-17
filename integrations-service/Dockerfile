# syntax=docker/dockerfile:1
# check=error=true

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies and FFmpeg with all required libraries
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libavcodec-extra \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.5.5 /uv /uvx /bin/

COPY integrations-service/.python-version integrations-service/pyproject.toml integrations-service/uv.lock ./
COPY julep_common /julep_common

RUN \
  uv sync --frozen --all-extras --no-group dev --color never --python-preference system

COPY integrations-service ./integrations-service

# Set proper signal handling
ENV PYTHONUNBUFFERED=1
ENV GUNICORN_CMD_ARGS="--capture-output --enable-stdio-inheritance"

# Run the application with proper signal handling
ENTRYPOINT ["uv", "run", "gunicorn", "integrations.web:app", "-c", "integrations-service/gunicorn_conf.py"]

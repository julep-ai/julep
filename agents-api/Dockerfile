# syntax=docker/dockerfile:1
# check=error=true

FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.5.5 /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libboost-all-dev \
    libc6-dev \
    libexpat1-dev \
    libffi-dev \
    liblzma-dev \
    libssl-dev \
    make \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

COPY .python-version pyproject.toml uv.lock ./

RUN \
  uv sync --frozen --all-extras --no-group dev --color never --python-preference system

COPY . ./

ENV PYTHONUNBUFFERED=1
ENV GUNICORN_CMD_ARGS="--capture-output --enable-stdio-inheritance"

ENTRYPOINT ["uv", "run", "gunicorn", "agents_api.web:app", "-c", "gunicorn_conf.py"]

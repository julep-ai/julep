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

# Verify FFmpeg installation
RUN ffmpeg -version

# Install Poetry
RUN pip install poetry

# Copy only requirements to cache them in docker layer
COPY pyproject.toml poetry.lock* /app/

# Project initialization:
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy project
COPY . ./

# Set proper signal handling
ENV PYTHONUNBUFFERED=1
ENV GUNICORN_CMD_ARGS="--capture-output --enable-stdio-inheritance"

# Run the application with proper signal handling
ENTRYPOINT ["gunicorn", "integrations.web:app", "-c", "gunicorn_conf.py"]
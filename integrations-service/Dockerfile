# syntax=docker/dockerfile:1
# check=error=true

FROM python:3.12-slim

WORKDIR /app

# Install Poetry globally without cache to reduce image size
RUN pip install --no-cache-dir poetry

# Copy only requirements to cache them in docker layer
COPY pyproject.toml poetry.lock* /app/

# Project initialization: 
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy the entire project directory
COPY . ./

# Run the application
ENTRYPOINT ["python", "-m", "integrations.web", "--host", "0.0.0.0", "--port", "8000"]

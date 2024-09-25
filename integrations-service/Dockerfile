FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy only requirements to cache them in docker layer
COPY pyproject.toml poetry.lock* /app/

# Project initialization:
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy project
COPY . ./

# Run the application
CMD ["python", "-m", "integrations.web", "--host", "0.0.0.0", "--port", "8000"]
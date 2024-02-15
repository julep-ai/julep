# Use vllm/vllm-openai:0.3.0 as a base image
FROM vllm/vllm-openai:v0.3.0 as builder

# Set environment variables
ENV PYTHONUNBUFFERED True
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

# Set the working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry==1.6.1

# Disable Poetry's virtual environment as Docker provides isolation
RUN poetry config virtualenvs.create false

# Copy only the Poetry configuration files
COPY pyproject.toml poetry.lock ./

# Install dependencies only, excluding the application itself
RUN poetry install --no-dev --no-root

# Copy the rest of your application code
COPY . .

# Now, install the application with Poetry, which will not re-install the dependencies
RUN poetry install --no-dev

# Define environment variables
ENV SENTRY_DSN=""
ENV API_KEY="xyz"
ENV HOST="0.0.0.0"
ENV PORT=8000
ENV BACKLOG=2048
ENV SKIP_CHECK_DEVELOPER_HEADERS=false
ENV TEMPERATURE_SCALING_FACTOR=1.0
ENV TEMPERATURE_SCALING_POWER=1.0
ENV MODEL_NAME=julep-ai/samantha-1-turbo
ENV HF_TOKEN=HUGGINGFACE_API_KEY
ENV HUGGING_FACE_HUB_TOKEN=HUGGINGFACE_API_KEY
# Define the entrypoint

ENTRYPOINT ["python3", "-m", "model_api", "--model", "julep-ai/samantha-1-turbo", "--tensor-parallel-size", "2", "--enforce-eager", "--dtype", "bfloat16"]

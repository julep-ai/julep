# Use vllm/vllm-openai:0.3.2 as a base image
FROM vllm/vllm-openai:v0.3.2 as builder

# Set environment variables
ENV PYTHONUNBUFFERED True
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

# Set the working directory
WORKDIR /app

# # Install libnccl2
# RUN apt-get update && apt-get install -y libnccl2

# Install Poetry
# Disable Poetry's virtual environment as Docker provides isolation
RUN pip install --no-cache-dir --upgrade poetry \
    && poetry config virtualenvs.create false

# Copy only the Poetry configuration files
COPY pyproject.toml poetry.lock ./

# Install dependencies only, excluding the application itself
RUN poetry install --no-dev --no-root

# Copy the rest of your application code
COPY . .

# Now, install the application with Poetry, which will not re-install the dependencies
RUN poetry install --no-dev

# Define the entrypoint
ENV MODEL julep-ai/samantha-1-turbo
ENV TP_SIZE 1
ENTRYPOINT python3 -m model_api --model $MODEL --tensor-parallel-size $TP_SIZE --enforce-eager --dtype bfloat16

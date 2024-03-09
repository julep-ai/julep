# Use vllm/vllm-openai:0.3.2 as a base image
FROM vllm/vllm-openai:v0.3.3 as builder

# Set environment variables
ENV PYTHONUNBUFFERED True
ENV POETRY_CACHE_DIR=/tmp/poetry_cache

# Set the working directory
WORKDIR /app

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
ENV MODEL_NAME julep-ai/samantha-1-turbo
ENV TP_SIZE 1
ENV MAX_MODEL_LEN 8192
ENV MAX_NUM_SEQS 1
ENV GPU_MEMORY_UTILIZATION 0.95
ENTRYPOINT python3 -m model_api --model $MODEL_NAME --tensor-parallel-size $TP_SIZE --enforce-eager --dtype bfloat16 --gpu-memory-utilization $GPU_MEMORY_UTILIZATION --max-model-len $MAX_MODEL_LEN --max-num-seqs $MAX_NUM_SEQS

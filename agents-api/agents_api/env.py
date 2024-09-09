"""
This module is responsible for loading and providing access to environment variables used throughout the agents-api application.
It utilizes the environs library for environment variable parsing.
"""

import random
from pprint import pprint
from typing import Any, Dict

from environs import Env

# Initialize the Env object for environment variable parsing.
env: Any = Env()

# App
# ---
multi_tenant_mode: bool = env.bool("AGENTS_API_MULTI_TENANT_MODE", default=False)
hostname: str = env.str("AGENTS_API_HOSTNAME", default="localhost")
public_port: int = env.int("AGENTS_API_PUBLIC_PORT", default=80)
api_prefix: str = env.str("AGENTS_API_PREFIX", default="")


# Tasks
# -----
task_max_parallelism: int = env.int("AGENTS_API_TASK_MAX_PARALLELISM", default=100)

# Debug
# -----
debug: bool = env.bool("AGENTS_API_DEBUG", default=False)
testing: bool = env.bool("AGENTS_API_TESTING", default=False)
sentry_dsn: str = env.str("SENTRY_DSN", default=None)


# Cozo
# ----
cozo_host: str = env.str("COZO_HOST", default="http://127.0.0.1:9070")
cozo_auth: str = env.str("COZO_AUTH_TOKEN", default=None)
summarization_model_name: str = env.str(
    "SUMMARIZATION_MODEL_NAME", default="gpt-4-turbo"
)


# Auth
# ----
_random_generated_key: str = "".join(str(random.randint(0, 9)) for _ in range(32))
api_key: str = env.str("AGENTS_API_KEY", _random_generated_key)

if api_key == _random_generated_key:
    print(f"Generated API key since not set in the environment: {api_key}")

api_key_header_name: str = env.str("AGENTS_API_KEY_HEADER_NAME", default="X-Auth-Key")

# Litellm API
# -----------
litellm_url: str = env.str("LITELLM_URL", default="http://0.0.0.0:4000")
litellm_master_key: str = env.str("LITELLM_MASTER_KEY", default="")


# Embedding service
# -----------------
embedding_service_base: str = env.str(
    "EMBEDDING_SERVICE_BASE", default="http://0.0.0.0:8082"
)
embedding_model_id: str = env.str(
    "EMBEDDING_MODEL_ID", default="Alibaba-NLP/gte-large-en-v1.5"
)
truncate_embed_text: bool = env.bool("TRUNCATE_EMBED_TEXT", default=True)


# Temporal
# --------
temporal_worker_url: str = env.str("TEMPORAL_WORKER_URL", default="localhost:7233")
temporal_namespace: str = env.str("TEMPORAL_NAMESPACE", default="default")
temporal_client_cert: str = env.str("TEMPORAL_CLIENT_CERT", default=None)
temporal_private_key: str = env.str("TEMPORAL_PRIVATE_KEY", default=None)
temporal_endpoint: Any = env.str("TEMPORAL_ENDPOINT", default="localhost:7233")
temporal_task_queue: Any = env.str("TEMPORAL_TASK_QUEUE", default="julep-task-queue")


# Consolidate environment variables
environment: Dict[str, Any] = dict(
    debug=debug,
    multi_tenant_mode=multi_tenant_mode,
    cozo_host=cozo_host,
    cozo_auth=cozo_auth,
    sentry_dsn=sentry_dsn,
    temporal_endpoint=temporal_endpoint,
    temporal_task_queue=temporal_task_queue,
    api_key=api_key,
    api_key_header_name=api_key_header_name,
    hostname=hostname,
    api_prefix=api_prefix,
    embedding_service_base=embedding_service_base,
    truncate_embed_text=truncate_embed_text,
    temporal_worker_url=temporal_worker_url,
    temporal_namespace=temporal_namespace,
    embedding_model_id=embedding_model_id,
    testing=testing,
)

# if debug or testing:
# Print the loaded environment variables for debugging purposes.
print("Environment variables:")
pprint(environment)
print()

# Yell if testing is enabled
print("@" * 80)
print(
    f"@@@ Running in {'testing' if testing else 'debug'} mode. This should not be enabled in production. @@@"
)
print("@" * 80)

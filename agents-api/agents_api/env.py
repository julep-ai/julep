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
protocol: str = env.str("AGENTS_API_PROTOCOL", default="http")
hostname: str = env.str("AGENTS_API_HOSTNAME", default="localhost")
public_port: int = env.int("AGENTS_API_PUBLIC_PORT", default=80)
api_prefix: str = env.str("AGENTS_API_PREFIX", default="")


# Tasks
# -----
task_max_parallelism: int = env.int("AGENTS_API_TASK_MAX_PARALLELISM", default=100)

# Blob Store
# ----------
use_blob_store_for_temporal: bool = env.bool(
    "USE_BLOB_STORE_FOR_TEMPORAL", default=False
)

blob_store_bucket: str = env.str("BLOB_STORE_BUCKET", default="agents-api")
blob_store_cutoff_kb: int = env.int("BLOB_STORE_CUTOFF_KB", default=1024)
s3_endpoint: str = env.str("S3_ENDPOINT", default="http://seaweedfs:8333")
s3_access_key: str | None = env.str("S3_ACCESS_KEY", default=None)
s3_secret_key: str | None = env.str("S3_SECRET_KEY", default=None)

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
do_verify_developer: bool = env.bool("DO_VERIFY_DEVELOPER", default=True)
do_verify_developer_owns_resource: bool = env.bool(
    "DO_VERIFY_DEVELOPER_OWNS_RESOURCE", default=True
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
embedding_model_id: str = env.str(
    "EMBEDDING_MODEL_ID", default="Alibaba-NLP/gte-large-en-v1.5"
)

embedding_dimensions: int = env.int("EMBEDDING_DIMENSIONS", default=1024)


# Integration service
# -------------------
integration_service_url: str = env.str(
    "INTEGRATION_SERVICE_URL", default="http://0.0.0.0:8000"
)


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
    temporal_worker_url=temporal_worker_url,
    temporal_namespace=temporal_namespace,
    embedding_model_id=embedding_model_id,
    testing=testing,
)

if debug or testing:
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

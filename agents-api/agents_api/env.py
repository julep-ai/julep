"""
This module is responsible for loading and providing access to environment variables used throughout the agents-api application.
It utilizes the environs library for environment variable parsing.
"""

import logging
import multiprocessing
import random
from pprint import pprint
from typing import TYPE_CHECKING, Any

from environs import Env

logger: logging.Logger = logging.getLogger(__name__)

# Initialize the Env object for environment variable parsing.
env: Any = Env()

# Debug
# -----
debug: bool = env.bool("AGENTS_API_DEBUG", default=False)
testing: bool = env.bool("AGENTS_API_TESTING", default=False)
sentry_dsn: str = env.str("SENTRY_DSN", default=None)

# App
# ---
multi_tenant_mode: bool = env.bool("AGENTS_API_MULTI_TENANT_MODE", default=False)
protocol: str = env.str("AGENTS_API_PROTOCOL", default="http")
hostname: str = env.str("AGENTS_API_HOSTNAME", default="localhost")
public_port: int = env.int("AGENTS_API_PUBLIC_PORT", default=80)
api_prefix: str = env.str("AGENTS_API_PREFIX", default="")
max_payload_size: int = env.int(
    "AGENTS_API_MAX_PAYLOAD_SIZE",
    default=50 * 1024 * 1024,  # 50MB
)
enable_backwards_compatibility_for_syntax: bool = env.bool(
    "ENABLE_BACKWARDS_COMPATIBILITY_FOR_SYNTAX", default=True
)
max_steps_accessible_in_tasks: int = env.int("MAX_STEPS_ACCESSIBLE_IN_TASKS", default=250)
gunicorn_cpu_divisor: int = env.int("GUNICORN_CPU_DIVISOR", default=4)
secrets_cache_ttl: int = env.int("SECRETS_CACHE_TTL", default=120)

raw_workers: str | None = env.str("GUNICORN_WORKERS", default=None)
if raw_workers and raw_workers.strip():
    gunicorn_workers: int = int(raw_workers)
else:
    gunicorn_workers: int = max(multiprocessing.cpu_count() // gunicorn_cpu_divisor, 1)


# Tasks
# -----
task_max_parallelism: int = env.int("AGENTS_API_TASK_MAX_PARALLELISM", default=100)
transition_requests_per_minute: int = env.int(
    "AGENTS_API_TRANSITION_REQUESTS_PER_MINUTE",
    default=500,
)


# Blob Store
# ----------
use_blob_store_for_temporal: bool = testing or env.bool(
    "USE_BLOB_STORE_FOR_TEMPORAL",
    default=False,
)

blob_store_bucket: str = env.str("BLOB_STORE_BUCKET", default="agents-api")
blob_store_cutoff_kb: int = env.int("BLOB_STORE_CUTOFF_KB", default=64)
s3_endpoint: str = env.str("S3_ENDPOINT", default="http://seaweedfs:8333")
s3_access_key: str | None = env.str("S3_ACCESS_KEY", default=None)
s3_secret_key: str | None = env.str("S3_SECRET_KEY", default=None)


# PostgreSQL
# ----
pg_dsn: str = env.str(
    "PG_DSN",
    default="postgres://postgres:postgres@0.0.0.0:5432/postgres?sslmode=disable",
)
summarization_model_name: str = env.str("SUMMARIZATION_MODEL_NAME", default="gpt-4-turbo")

query_timeout: float = env.float("QUERY_TIMEOUT", default=90.0)
pool_max_size: int = min(env.int("POOL_MAX_SIZE", default=multiprocessing.cpu_count()), 10)


# Auth
# ----
_random_generated_key: str = "".join(str(random.randint(0, 9)) for _ in range(32))
api_key: str = env.str("AGENTS_API_KEY", _random_generated_key)

if api_key == _random_generated_key and not TYPE_CHECKING:
    # AIDEV-NOTE: avoid printing API keys; log generic warning only
    logger.warning("Generated API key since not set in the environment.")

api_key_header_name: str = env.str("AGENTS_API_KEY_HEADER_NAME", default="X-Auth-Key")

max_free_sessions: int = env.int("MAX_FREE_SESSIONS", default=50)
max_free_executions: int = env.int("MAX_FREE_EXECUTIONS", default=50)

# Usage limits
# -----------
free_tier_cost_limit: float = env.float("FREE_TIER_COST_LIMIT", default=2.0)

# Litellm API
# -----------
litellm_url: str | None = env.str("LITELLM_URL", default=None)
litellm_master_key: str = env.str("LITELLM_MASTER_KEY", default="")


# Embedding service
# -----------------
embedding_model_id: str = env.str("EMBEDDING_MODEL_ID", default="openai/text-embedding-3-large")

embedding_dimensions: int = env.int("EMBEDDING_DIMENSIONS", default=1024)


# Integration service
# -------------------
integration_service_url: str = env.str("INTEGRATION_SERVICE_URL", default="http://0.0.0.0:8000")


# Temporal
# --------
temporal_worker_url: str = env.str("TEMPORAL_WORKER_URL", default="localhost:7233")
temporal_namespace: str = env.str("TEMPORAL_NAMESPACE", default="default")
temporal_client_cert: str = env.str("TEMPORAL_CLIENT_CERT", default=None)
temporal_private_key: str = env.str("TEMPORAL_PRIVATE_KEY", default=None)
temporal_api_key: str = env.str("TEMPORAL_API_KEY", default=None)
temporal_endpoint: Any = env.str("TEMPORAL_ENDPOINT", default="localhost:7233")
temporal_task_queue: Any = env.str("TEMPORAL_TASK_QUEUE", default="julep-task-queue")
temporal_schedule_to_close_timeout: int = env.int(
    "TEMPORAL_SCHEDULE_TO_CLOSE_TIMEOUT",
    default=3600,
)
temporal_heartbeat_timeout: int = env.int("TEMPORAL_HEARTBEAT_TIMEOUT", default=900)
temporal_metrics_bind_host: str = env.str("TEMPORAL_METRICS_BIND_HOST", default="0.0.0.0")
temporal_metrics_bind_port: int = env.int("TEMPORAL_METRICS_BIND_PORT", default=14000)
temporal_activity_after_retry_timeout: int = env.int(
    "TEMPORAL_ACTIVITY_AFTER_RETRY_TIMEOUT",
    default=30,
)
temporal_search_attribute_key: str = env.str(
    "TEMPORAL_SEARCH_ATTRIBUTE_KEY",
    default="CustomStringField",
)


def _parse_optional_int(val: str | None) -> int | None:
    if not val or val.lower() == "none":
        return None
    return int(val)


# Temporal worker configuration
temporal_max_concurrent_workflow_tasks: int | None = _parse_optional_int(
    env.str("TEMPORAL_MAX_CONCURRENT_WORKFLOW_TASKS", default=None),
)

temporal_max_concurrent_activities: int | None = _parse_optional_int(
    env.str("TEMPORAL_MAX_CONCURRENT_ACTIVITIES", default=None),
)

temporal_max_activities_per_second: int | None = _parse_optional_int(
    env.str("TEMPORAL_MAX_ACTIVITIES_PER_SECOND", default=None),
)

temporal_max_task_queue_activities_per_second: int | None = _parse_optional_int(
    env.str("TEMPORAL_MAX_TASK_QUEUE_ACTIVITIES_PER_SECOND", default=None),
)

# API Keys needed for the `humanize_text` method in `evaluate` step
# ------------
sapling_api_key: str = env.str("SAPLING_API_KEY", default=None)
zerogpt_api_key: str = env.str("ZEROGPT_API_KEY", default=None)
zerogpt_url: str = env.str(
    "ZEROGPT_URL", default="https://api.zerogpt.com/api/detect/detectText"
)
desklib_url: str = env.str("DESKLIB_URL", default="http://35.243.190.233/detect")
sapling_url: str = env.str("SAPLING_URL", default="https://api.sapling.ai/api/v1/aidetect")
brave_api_key: str = env.str("BRAVE_API_KEY", default=None)
# Responses Flag
# ---------------
enable_responses: bool = env.bool("ENABLE_RESPONSES", default=False)


# Secrets
# -------
def _validate_master_key(key: str | None) -> str:
    """Validate that the master key is the correct length for encryption and is provided."""
    if key is None or len(key) != 32:
        msg = "SECRETS_MASTER_KEY must be exactly 32 characters long"
        raise ValueError(msg)
    return key


if not TYPE_CHECKING and not testing:
    secrets_master_key: str = _validate_master_key(env.str("SECRETS_MASTER_KEY"))

else:
    secrets_master_key: str = "*" * 32
    print("USING FAKE SECRETS KEY FOR TESTING")

# Consolidate environment variables
environment: dict[str, Any] = {
    "debug": debug,
    "multi_tenant_mode": multi_tenant_mode,
    "sentry_dsn": sentry_dsn,
    "temporal_endpoint": temporal_endpoint,
    "temporal_task_queue": temporal_task_queue,
    "api_key": api_key,
    "api_key_header_name": api_key_header_name,
    "hostname": hostname,
    "api_prefix": api_prefix,
    "temporal_worker_url": temporal_worker_url,
    "temporal_namespace": temporal_namespace,
    "embedding_model_id": embedding_model_id,
    "use_blob_store_for_temporal": use_blob_store_for_temporal,
    "blob_store_bucket": blob_store_bucket,
    "blob_store_cutoff_kb": blob_store_cutoff_kb,
    "s3_endpoint": s3_endpoint,
    "s3_access_key": s3_access_key,
    "s3_secret_key": s3_secret_key,
    "testing": testing,
    "enable_responses": enable_responses,
    "free_tier_cost_limit": free_tier_cost_limit,
    "secrets_master_key": secrets_master_key,
}

if debug or testing:
    # Print the loaded environment variables for debugging purposes.
    print("Environment variables:")
    pprint(environment)
    print()

    # Yell if testing is enabled
    print("@" * 80)
    print(
        f"@@@ Running in {'testing' if testing else 'debug'} mode. This should not be enabled in production. @@@",
    )
    print("@" * 80)

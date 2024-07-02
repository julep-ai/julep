"""
This module is responsible for loading and providing access to environment variables used throughout the agents-api application.
It utilizes the environs library for environment variable parsing.
"""

from pprint import pprint
from environs import Env


# Initialize the Env object for environment variable parsing.
env = Env()
env.read_env()

# Debug mode
debug: bool = env.bool("AGENTS_API_DEBUG", default=False)

# Base URL for the COZO service. Defaults to the local development URL if not specified.
cozo_host: str = env.str("COZO_HOST", default="http://127.0.0.1:9070")
cozo_auth: str = env.str("COZO_AUTH_TOKEN", default=None)
prediction_project: str = env.str("PREDICTION_PROJECT", default=None)
prediction_endpoint_id: str = env.str("PREDICTION_ENDPOINT_ID", default=None)
prediction_location: str = env.str("PREDICTION_LOCATION", default="us-central1")
prediction_api_endpoint: str = env.str(
    "PREDICTION_API_ENDPOINT", default="us-central1-aiplatform.googleapis.com"
)
model_api_key: str = env.str("MODEL_API_KEY", default=None)
model_inference_url: str = env.str("MODEL_INFERENCE_URL", default=None)
openai_api_key: str = env.str("OPENAI_API_KEY", default="")
summarization_model_name: str = env.str(
    "SUMMARIZATION_MODEL_NAME", default="gpt-4-turbo"
)
worker_url: str = env.str("WORKER_URL", default=None)

sentry_dsn: str = env.str("SENTRY_DSN", default=None)

# Temporal
temporal_endpoint = env.str("TEMPORAL_ENDPOINT", default="localhost:7233")
temporal_task_queue = env.str("TEMPORAL_TASK_QUEUE", default="memory-task-queue")

# auth
api_key: str = env.str("AGENTS_API_KEY")
api_key_header_name: str = env.str("AGENTS_API_KEY_HEADER_NAME", default="X-Auth-Key")
skip_check_developer_headers: bool = env.bool(
    "SKIP_CHECK_DEVELOPER_HEADERS", default=False
)

embedding_service_url: str = env.str(
    "EMBEDDING_SERVICE_URL", default="http://0.0.0.0:8083/embed"
)


embedding_model_id: str = env.str("EMBEDDING_MODEL_ID", default="BAAI/bge-m3")

truncate_embed_text: bool = env.bool("TRUNCATE_EMBED_TEXT", default=False)

# Temporal
temporal_worker_url: str = env.str("TEMPORAL_WORKER_URL", default="localhost:7233")
temporal_namespace: str = env.str("TEMPORAL_NAMESPACE", default="default")
temporal_client_cert: str = env.str("TEMPORAL_CLIENT_CERT", default=None)
temporal_private_key: str = env.str("TEMPORAL_PRIVATE_KEY", default=None)

# Consolidate environment variables into a dictionary for easy access and debugging.
environment = dict(
    debug=debug,
    cozo_host=cozo_host,
    cozo_auth=cozo_auth,
    worker_url=worker_url,
    sentry_dsn=sentry_dsn,
    temporal_endpoint=temporal_endpoint,
    temporal_task_queue=temporal_task_queue,
    api_key=api_key,
    api_key_header_name=api_key_header_name,
    skip_check_developer_headers=skip_check_developer_headers,
    embedding_service_url=embedding_service_url,
    truncate_embed_text=truncate_embed_text,
    temporal_worker_url=temporal_worker_url,
    temporal_namespace=temporal_namespace,
    openai_api_key=openai_api_key,
    docs_embedding_service_url=embedding_service_url,
    embedding_model_id=embedding_model_id,
)

if openai_api_key == "":
    print("OpenAI API key not found. OpenAI API will not be enabled.")

if debug:
    # Print the loaded environment variables for debugging purposes.
    print("Environment variables:")
    pprint(environment)
    print()

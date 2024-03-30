from pprint import pprint
from environs import Env


env = Env()
env.read_env()


cozo_host: str = env.str("COZO_HOST", default="http://127.0.0.1:9070")
cozo_auth: str = env.str("COZO_AUTH_TOKEN", default=None)
prediction_project: str = env.str("PREDICTION_PROJECT", default=None)
prediction_endpoint_id: str = env.str("PREDICTION_ENDPOINT_ID", default=None)
prediction_location: str = env.str("PREDICTION_LOCATION", default="us-central1")
prediction_api_endpoint: str = env.str(
    "PREDICTION_API_ENDPOINT", default="us-central1-aiplatform.googleapis.com"
)
generation_url: str = env.str("GENERATION_URL", default=None)
generation_auth_token: str = env.str("GENERATION_AUTH_TOKEN", default=None)
summarization_ratio_threshold: float = env.float(
    "MAX_TOKENS_RATIO_TO_SUMMARIZE", default=0.5
)
summarization_tokens_threshold: int = env.int(
    "SUMMARIZATION_TOKENS_THRESHOLD", default=2048
)
worker_url: str = env.str("WORKER_URL", default=None)

# principles you API
client_id: str = env.str("PRINCIPLES_YOU_CLIENT_ID", default=None)
client_secret: str = env.str("PRINCIPLES_YOU_CLIENT_SECRET", default=None)
endpoint_base: str = env.str(
    "PRINCIPLES_YOU_ENDPOINT_BASE", default="https://app.stg40.principles.com"
)
cogito_endpoint: str = env.str(
    "PRINCIPLES_YOU_COGITO_ENDPOINT",
    default="principles-stg-primary.auth.us-east-1.amazoncognito.com/oauth2/token",
)

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

# embedding service URL
embedding_service_url: str = env.str(
    "EMBEDDING_SERVICE_URL", default="http://0.0.0.0:8082/embed"
)

truncate_embed_text: bool = env.bool("TRUNCATE_EMBED_TEXT", default=False)

# Temporal
temporal_worker_url: str = env.str("TEMPORAL_WORKER_URL", default="localhost:7233")
temporal_namespace: str = env.str("TEMPORAL_NAMESPACE", default="default")
temporal_client_cert: str = env.str("TEMPORAL_CLIENT_CERT", default=None)
temporal_private_key: str = env.str("TEMPORAL_PRIVATE_KEY", default=None)

environment = dict(
    cozo_host=cozo_host,
    cozo_auth=cozo_auth,
    generation_url=generation_url,
    generation_auth_token=generation_auth_token,
    summarization_ratio_threshold=summarization_ratio_threshold,
    summarization_tokens_threshold=summarization_tokens_threshold,
    worker_url=worker_url,
    endpoint_base=endpoint_base,
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
)

print("Environment variables:")
pprint(environment)
print()

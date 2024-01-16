from environs import Env


env = Env()
env.read_env()


cozo_host: str = env.str("COZO_HOST", default="http://127.0.0.1:9070")
cozo_auth: str = env.str("COZO_AUTH", default=None)
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
api_key: str = env.str("API_KEY")

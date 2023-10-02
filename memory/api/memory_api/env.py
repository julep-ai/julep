from environs import Env


env = Env()
env.read_env()


cozo_host: str = env.str("COZO_HOST", default="http://127.0.0.1:9070")
cozo_auth: str = env.str("COZO_AUTH", default=None)
prediction_project: str = env.str("PREDICTION_PROJECT")
prediction_endpoint_id: str = env.str("PREDICTION_ENDPOINT_ID")
prediction_location: str = env.str("PREDICTION_LOCATION", default="us-central1")
prediction_api_endpoint: str = env.str("PREDICTION_API_ENDPOINT", default="us-central1-aiplatform.googleapis.com")
generation_url: str = env.str("GENERATION_URL")
generation_auth_token: str = env.str("GENERATION_AUTH_TOKEN")
summarization_ratio_threshold: float = env.float("MAX_TOKENS_RATIO_TO_SUMMARIZE", default=0.5)
worker_url: str = env.str("WORKER_URL")
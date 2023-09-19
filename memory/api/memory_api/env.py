from environs import Env


env = Env()
env.read_env()


cozo_host: str = env.str("COZO_HOST")
cozo_auth: str = env.str("COZO_AUTH", default=None)
prediction_project: str = env.str("PREDICTION_PROJECT")
prediction_endpoint_id: str = env.str("PREDICTION_ENDPOINT_ID")
prediction_location: str = env.str("PREDICTION_LOCATION", default="us-central1")
prediction_api_endpoint: str = env.str("PREDICTION_API_ENDPOINT", default="us-central1-aiplatform.googleapis.com")
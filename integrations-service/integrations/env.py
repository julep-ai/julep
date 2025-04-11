import multiprocessing

from environs import Env

# Initialize the Env object for environment variable parsing.
env = Env()
env.read_env()  # Read .env file, if it exists

# Load environment variables
browserbase_api_key = env.str("BROWSERBASE_API_KEY", default=None)
browserbase_project_id = env.str("BROWSERBASE_PROJECT_ID", default=None)
openweather_api_key = env.str("OPENWEATHER_API_KEY", default=None)
spider_api_key = env.str("SPIDER_API_KEY", default=None)
brave_api_key = env.str("BRAVE_API_KEY", default=None)
llama_api_key = env.str("LLAMA_API_KEY", default=None)
cloudinary_api_key = env.str("CLOUDINARY_API_KEY", default=None)
cloudinary_api_secret = env.str("CLOUDINARY_API_SECRET", default=None)
cloudinary_cloud_name = env.str("CLOUDINARY_CLOUD_NAME", default=None)
mailgun_password = env.str("MAILGUN_PASSWORD", default=None)
sentry_dsn: str = env.str("SENTRY_DSN", default=None)
unstructured_api_key = env.str("UNSTRUCTURED_API_KEY", default=None)
algolia_api_key = env.str("ALGOLIA_API_KEY", default=None)
algolia_application_id = env.str("ALGOLIA_APPLICATION_ID", default=None)

# Gunicorn
gunicorn_cpu_divisor: int = env.int("GUNICORN_CPU_DIVISOR", default=4)

raw_workers: str | None = env.str("GUNICORN_WORKERS", default=None)
if raw_workers and raw_workers.strip():
    gunicorn_workers: int = int(raw_workers)
else:
    gunicorn_workers: int = max(multiprocessing.cpu_count() // gunicorn_cpu_divisor, 1)

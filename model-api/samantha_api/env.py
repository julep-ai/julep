from environs import Env


env = Env()
env.read_env()


sentry_dsn: str = env.str("SENTRY_DSN", default="")
api_key: str = env.str("API_KEY")

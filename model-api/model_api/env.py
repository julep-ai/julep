from environs import Env


env = Env()
env.read_env()


sentry_dsn: str = env.str("SENTRY_DSN", default="")
api_key: str = env.str("API_KEY")
host: str = env.str("HOST", default="0.0.0.0")
port: int = env.int("PORT", default=8000)
backlog: int = env.int("BACKLOG", default=2048)

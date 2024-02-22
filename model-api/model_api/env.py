from pprint import pprint

from environs import Env


env = Env()
env.read_env()


sentry_dsn: str = env.str("SENTRY_DSN", default="")
api_key: str = env.str("API_KEY")
api_key_header_name: str = env.str("API_KEY_HEADER_NAME", default="X-Auth-Key")
host: str = env.str("HOST", default="0.0.0.0")
port: int = env.int("PORT", default=8000)
backlog: int = env.int("BACKLOG", default=2048)
skip_check_developer_headers: bool = env.bool(
    "SKIP_CHECK_DEVELOPER_HEADERS", default=False
)
temperature_scaling_factor: float = env.float("TEMPERATURE_SCALING_FACTOR", default=1.0)
temperature_scaling_power: float = env.float("TEMPERATURE_SCALING_POWER", default=1.0)

environment = dict(
    sentry_dsn=sentry_dsn,
    api_key=api_key,
    host=host,
    port=port,
    backlog=backlog,
    skip_check_developer_headers=skip_check_developer_headers,
    temperature_scaling_factor=temperature_scaling_factor,
    temperature_scaling_power=temperature_scaling_power,
)

print("Environment variables:")
pprint(environment)
print()

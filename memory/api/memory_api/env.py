from environs import Env


env = Env()
env.read_env()


cozo_host: str = env.str("COZO_HOST")
cozo_auth: str = env.str("COZO_AUTH", default=None)

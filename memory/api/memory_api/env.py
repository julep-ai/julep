from environs import Env


env = Env()
env.read_env()


cozo_host: str = env.bool("COZO_HOST")
cozo_auth: str = env.json("COZO_AUTH", default=None)

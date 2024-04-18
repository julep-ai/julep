from typing import Optional

from environs import Env

from .api.environment import JulepApiEnvironment

# Initialize the environment variable handler.
env = Env()

# Optional environment variable for the Julep API key. Defaults to None if not set.
JULEP_API_KEY: Optional[str] = env.str("JULEP_API_KEY", None)
# Optional environment variable for the Julep API URL. Defaults to the Julep API's default environment URL if not set.
JULEP_API_URL: Optional[str] = env.str(
    "JULEP_API_URL", JulepApiEnvironment.DEFAULT.value
)

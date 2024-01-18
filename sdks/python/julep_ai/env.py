from typing import Optional

from environs import Env

env = Env()

JULEP_API_KEY: Optional[str] = env.str("JULEP_API_KEY", None)
JULEP_API_URL: Optional[str] = env.str("JULEP_API_URL", "https://api-alpha.julep.ai")

from functools import partial
from litellm import acompletion as _acompletion

from ..env import litellm_master_key, litellm_url

__all__ = ["acompletion"]

acompletion = partial(_acompletion, api_base=litellm_url, api_key=litellm_master_key)
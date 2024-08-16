from functools import wraps

from litellm import acompletion as _acompletion
from litellm.utils import CustomStreamWrapper, ModelResponse

from ..env import litellm_master_key, litellm_url

__all__ = ["acompletion"]


@wraps(_acompletion)
async def acompletion(*, model: str, **kwargs) -> ModelResponse | CustomStreamWrapper:
    return await _acompletion(
        model=f"openai/{model}",  # This is here because litellm proxy expects this format
        **kwargs,
        api_base=litellm_url,
        api_key=litellm_master_key,
    )

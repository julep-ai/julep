from functools import wraps
from typing import List

from beartype import beartype
from litellm import acompletion as _acompletion
from litellm import get_supported_openai_params
from litellm.utils import CustomStreamWrapper, ModelResponse

from ..env import litellm_master_key, litellm_url

__all__: List[str] = ["acompletion"]


@wraps(_acompletion)
@beartype
async def acompletion(
    *, model: str, messages: list[dict], custom_api_key: None | str = None, **kwargs
) -> ModelResponse | CustomStreamWrapper:

    supported_params = get_supported_openai_params(model)
    settings = {k: v for k, v in kwargs.items() if k in supported_params}

    return await _acompletion(
        model=model,
        messages=messages,
        **settings,
        base_url=None if custom_api_key else litellm_url,
        api_key=custom_api_key or litellm_master_key,
    )

from functools import wraps
from typing import List, Literal

import litellm
from beartype import beartype
from litellm import (
    acompletion as _acompletion,
)
from litellm import (
    aembedding as _aembedding,
)
from litellm import (
    get_supported_openai_params,
)
from litellm.utils import CustomStreamWrapper, ModelResponse

from ..env import (
    embedding_dimensions,
    embedding_model_id,
    litellm_master_key,
    litellm_url,
)

__all__: List[str] = ["acompletion"]

# TODO: Should check if this is really needed
litellm.drop_params = True


@wraps(_acompletion)
@beartype
async def acompletion(
    *, model: str, messages: list[dict], custom_api_key: None | str = None, **kwargs
) -> ModelResponse | CustomStreamWrapper:
    if not custom_api_key:
        model = f"openai/{model}"  # FIXME: This is for litellm

    supported_params = get_supported_openai_params(model)
    settings = {k: v for k, v in kwargs.items() if k in supported_params}

    return await _acompletion(
        model=model,
        messages=messages,
        **settings,
        base_url=None if custom_api_key else litellm_url,
        api_key=custom_api_key or litellm_master_key,
    )


@wraps(_aembedding)
@beartype
async def aembedding(
    *,
    inputs: str | list[str],
    model: str = embedding_model_id,
    dimensions: int = embedding_dimensions,
    join_inputs: bool = False,
    custom_api_key: None | str = None,
    **settings,
) -> list[list[float]]:
    # Temporarily commented out (causes errors when using voyage/voyage-3)
    # if not custom_api_key:
    # model = f"openai/{model}"  # FIXME: This is for litellm

    if isinstance(inputs, str):
        input = [inputs]
    else:
        input = ["\n\n".join(inputs)] if join_inputs else inputs

    response = await _aembedding(
        model=model,
        input=input,
        # dimensions=dimensions,  # FIXME: litellm doesn't support dimensions correctly
        api_base=None if custom_api_key else litellm_url,
        api_key=custom_api_key or litellm_master_key,
        drop_params=True,
        **settings,
    )

    embedding_list: list[dict[Literal["embedding"], list[float]]] = response.data

    # FIXME: Truncation should be handled by litellm
    result = [embedding["embedding"][:dimensions] for embedding in embedding_list]

    return result

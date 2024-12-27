from functools import wraps
from typing import Literal

from beartype import beartype
from litellm import acompletion as _acompletion
from litellm import aembedding as _aembedding
from litellm import get_supported_openai_params
from litellm.utils import CustomStreamWrapper, ModelResponse

from ..env import (
    embedding_dimensions,
    embedding_model_id,
    litellm_master_key,
    litellm_url,
)

__all__: list[str] = ["acompletion"]


def patch_litellm_response(
    model_response: ModelResponse | CustomStreamWrapper,
) -> ModelResponse | CustomStreamWrapper:
    """
    Patches the response we get from litellm to handle unexpected response formats.
    """

    if isinstance(model_response, ModelResponse):
        for choice in model_response.choices:
            if choice.finish_reason == "eos":
                choice.finish_reason = "stop"

    elif (
        isinstance(model_response, CustomStreamWrapper)
        and model_response.received_finish_reason == "eos"
    ):
        model_response.received_finish_reason = "stop"

    return model_response


@wraps(_acompletion)
@beartype
async def acompletion(
    *, model: str, messages: list[dict], custom_api_key: str | None = None, **kwargs
) -> ModelResponse | CustomStreamWrapper:
    if not custom_api_key:
        model = f"openai/{model}"  # This is needed for litellm

    supported_params = get_supported_openai_params(model)
    settings = {k: v for k, v in kwargs.items() if k in supported_params}

    # NOTE: This is a fix for Mistral API, which expects a different message format
    if model[7:].startswith("mistral"):
        messages = [
            {"role": message["role"], "content": message["content"]} for message in messages
        ]

    model_response = await _acompletion(
        model=model,
        messages=messages,
        **settings,
        base_url=None if custom_api_key else litellm_url,
        api_key=custom_api_key or litellm_master_key,
    )

    return patch_litellm_response(model_response)


@wraps(_aembedding)
@beartype
async def aembedding(
    *,
    inputs: str | list[str],
    model: str = embedding_model_id,
    embed_instruction: str | None = None,
    dimensions: int = embedding_dimensions,
    join_inputs: bool = False,
    custom_api_key: str | None = None,
    **settings,
) -> list[list[float]]:
    # Temporarily commented out (causes errors when using voyage/voyage-3)
    # if not custom_api_key:
    # model = f"openai/{model}"  # FIXME: Is this still needed for litellm?

    input = (
        [inputs]
        if isinstance(inputs, str)
        else ["\n\n".join(inputs)]
        if join_inputs
        else inputs
    )

    if embed_instruction:
        input = [embed_instruction, *input]

    response = await _aembedding(
        model=model,
        input=input,
        api_base=None if custom_api_key else litellm_url,
        api_key=custom_api_key or litellm_master_key,
        drop_params=True,
        **settings,
    )

    embedding_list: list[dict[Literal["embedding"], list[float]]] = response.data

    return [
        item["embedding"][:dimensions]
        for item in embedding_list
        if len(item["embedding"]) > dimensions
    ]

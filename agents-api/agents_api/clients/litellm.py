from functools import wraps
from typing import Literal

import aiohttp
from beartype import beartype
from litellm import acompletion as _acompletion
from litellm import aembedding as _aembedding
from litellm import get_supported_openai_params
from litellm.utils import CustomStreamWrapper, ModelResponse, get_valid_models

from ..env import (
    embedding_dimensions,
    embedding_model_id,
    litellm_master_key,
    litellm_url,
    enable_responses,
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
    *,
    model: str,
    messages: list[dict],
    custom_api_key: str | None = None,
    **kwargs,
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

    for message in messages:
        if "tool_calls" in message and message["tool_calls"] == []:
            message.pop("tool_calls")

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
    if not custom_api_key:
        model = f"openai/{model}"  # This is needed for litellm

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

    # Truncate the embedding to the specified dimensions
    return [
        item["embedding"][:dimensions]
        for item in embedding_list
        if len(item["embedding"]) >= dimensions
    ]


@beartype
async def get_model_list(*, custom_api_key: str | None = None) -> list[dict]:
    """
    Fetches the list of available models from the LiteLLM server.

    Returns:
        list[dict]: A list of model information dictionaries
    """

    if enable_responses:
        ret = get_valid_models()
        return [{"id": model_name} for model_name in ret]
    
    headers = {"accept": "application/json", "x-api-key": custom_api_key or litellm_master_key}

    async with (
        aiohttp.ClientSession() as session,
        session.get(
            url=f"{litellm_url}/models" if not custom_api_key else "/models",
            headers=headers,
        ) as response,
    ):
        response.raise_for_status()
        data = await response.json()
        return data["data"]

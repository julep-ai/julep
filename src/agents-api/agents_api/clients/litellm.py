import contextlib
from functools import wraps
from typing import Literal
from uuid import UUID

import aiohttp
from beartype import beartype
from litellm import acompletion as _acompletion
from litellm import aembedding as _aembedding
from litellm import get_supported_openai_params
from litellm.utils import CustomStreamWrapper, ModelResponse, get_valid_models

from ..common.exceptions.secrets import (
    SecretNotFoundError,  # AIDEV-NOTE: catch missing secrets in LLM client
)
from ..common.utils.llm_providers import get_api_key_env_var_name, get_litellm_model_name
from ..common.utils.secrets import get_secret_by_name
from ..common.utils.usage import track_embedding_usage, track_usage
from ..env import (
    embedding_dimensions,
    embedding_model_id,
    enable_responses,
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
    *,
    model: str,
    messages: list[dict],
    custom_api_key: str | None = None,
    **kwargs,
) -> ModelResponse | CustomStreamWrapper:
    api_user = kwargs.get("user")

    # Check if user has a custom API key in secrets
    api_key_env_var_name = get_api_key_env_var_name(model)
    secret = None

    if api_user is not None and api_key_env_var_name:
        developer_id: UUID = UUID(api_user)

        with contextlib.suppress(SecretNotFoundError):
            secret = await get_secret_by_name(
                developer_id=developer_id,
                name=api_key_env_var_name,
                decrypt=True,
            )

    # Determine if we have a custom API key (either provided or from secrets)
    has_custom_key = custom_api_key or (secret and secret.value)

    if has_custom_key:
        # User has their own API key - convert model name and use direct provider
        if not custom_api_key and secret:
            custom_api_key = secret.value
        model = get_litellm_model_name(model)
    else:
        # No custom key - use our proxy with openai/ prefix
        model = f"openai/{model}"

    supported_params: list[str] = (
        get_supported_openai_params(model) or []
    )  # Supported params returns Optional[list[str]]
    supported_params += ["user", "mock_response", "stream_options"]
    settings = {k: v for k, v in kwargs.items() if k in supported_params}

    # NOTE: This is a fix for Mistral API, which expects a different message format
    if model[7:].startswith("mistral"):
        messages = [
            {"role": message["role"], "content": message["content"]} for message in messages
        ]

    for message in messages:
        if "tool_calls" in message and message["tool_calls"] == []:
            message.pop("tool_calls")
    tools_free_models = {"openai/gpt-5-chat-latest"}
    if model in tools_free_models:
        settings.pop("tools", None)
        kwargs.pop("tools", None)

    model_response = await _acompletion(
        model=model,
        messages=messages,
        **settings,
        base_url=None if has_custom_key else litellm_url,
        api_key=custom_api_key or litellm_master_key,
    )

    response = patch_litellm_response(model_response)

    # Track usage in database if we have a user ID (which should be the developer ID)
    user = settings.get("user")
    if user and isinstance(response, ModelResponse):
        try:
            model = response.model
            await track_usage(
                developer_id=UUID(user),
                model=model,
                messages=messages,
                response=response,
                custom_api_used=custom_api_key is not None,
                metadata={"tags": kwargs.get("tags", [])},
            )
        except Exception as e:
            # Log error but don't fail the request if usage tracking fails
            print(f"Error tracking usage: {e}")

    return response

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
    # Check if user has a custom API key in secrets
    api_user = settings.get("user")
    api_key_env_var_name = get_api_key_env_var_name(model)
    secret = None

    if api_user is not None and api_key_env_var_name:
        developer_id: UUID = UUID(api_user)

        with contextlib.suppress(SecretNotFoundError):
            secret = await get_secret_by_name(
                developer_id=developer_id,
                name=api_key_env_var_name,
                decrypt=True,
            )

    # Determine if we have a custom API key (either provided or from secrets)
    has_custom_key = custom_api_key or (secret and secret.value)

    if has_custom_key:
        # User has their own API key - convert model name and use direct provider
        if not custom_api_key and secret:
            custom_api_key = secret.value
        model = get_litellm_model_name(model)
    else:
        # No custom key - use our proxy with openai/ prefix
        model = f"openai/{model}"

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
        api_base=None if has_custom_key else litellm_url,
        api_key=custom_api_key or litellm_master_key,
        drop_params=True,
        **settings,
    )

    # Track embedding usage if we have a user ID
    user = settings.get("user")
    if user:
        try:
            model = response.model
            await track_embedding_usage(
                developer_id=UUID(user),
                model=model,
                inputs=input,
                response=response,
                custom_api_used=bool(custom_api_key),
                metadata={
                    "request_id": response.id if hasattr(response, "id") else None,
                    "embedding_count": len(input),
                    "tags": settings.get("tags", []),
                },
            )
        except Exception as e:
            # Log error but don't fail the request if usage tracking fails
            print(f"Error tracking embedding usage: {e}")

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

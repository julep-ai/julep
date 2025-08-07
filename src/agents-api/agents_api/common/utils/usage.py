"""
Utilities for tracking token usage and costs for LLM API calls.
"""

from typing import Any
from uuid import UUID

from beartype import beartype
from litellm.utils import ModelResponse, token_counter

from ...queries.usage.create_usage_record import create_usage_record


async def is_llama_based_model(model_string: str) -> bool:
    """Check if a model string (either model_name or litellm_params.model) indicates a LLaMA model"""
    model_lower = model_string.lower()
    return "llama" in model_lower or model_lower.startswith("l3.") or "/l3." in model_lower


@beartype
async def track_usage(
    *,
    developer_id: UUID,
    model: str,
    messages: list[dict],
    response: ModelResponse,
    custom_api_used: bool = False,
    metadata: dict[str, Any] = {},
    connection_pool: Any = None,  # This is for testing purposes
) -> None:
    """
    Tracks token usage and costs for an LLM API call.

    Parameters:
        developer_id (UUID): The unique identifier for the developer.
        model (str): The model used for the API call.
        messages (list[dict]): The messages sent to the model.
        response (ModelResponse): The response from the LLM API call.
        custom_api_used (bool): Whether a custom API key was used.
        metadata (dict): Additional metadata about the usage.

    Returns:
        None
    """

    # Try to get token counts from response.usage
    if response.usage:
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
    else:
        # Calculate tokens manually if usage is not available
        prompt_tokens = token_counter(model=model, messages=messages)

        # Calculate completion tokens from the response
        completion_content = [
            {"content": choice.message.content}
            for choice in response.choices
            if hasattr(choice, "message")
            and choice.message
            and hasattr(choice.message, "content")
            and choice.message.content
        ]

        completion_tokens = (
            token_counter(model=model, messages=completion_content) if completion_content else 0
        )

    # Map the model name to the actual model name
    actual_model = model

    is_llama_model = await is_llama_based_model(actual_model)

    # Create usage record
    await create_usage_record(
        developer_id=developer_id,
        model=actual_model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        custom_api_used=custom_api_used,
        metadata={
            "request_id": response.id if hasattr(response, "id") else None,
            **metadata,
        },
        is_llama_model=is_llama_model,
        connection_pool=connection_pool,
    )


@beartype
async def track_embedding_usage(
    *,
    developer_id: UUID,
    model: str,
    inputs: list[str],
    response: Any,
    custom_api_used: bool = False,
    metadata: dict[str, Any] = {},
) -> None:
    """
    Tracks token usage and costs for an embedding API call.

    Parameters:
        developer_id (UUID): The unique identifier for the developer.
        model (str): The model used for the embedding.
        inputs (list[str]): The inputs sent for embedding.
        response (Any): The response from the embedding API call.
        custom_api_used (bool): Whether a custom API key was used.
        metadata (dict): Additional metadata about the usage.

    Returns:
        None
    """

    # Try to get token count from response.usage
    if hasattr(response, "usage") and response.usage:
        prompt_tokens = response.usage.prompt_tokens
    else:
        # Calculate tokens manually if usage is not available
        prompt_tokens = sum(
            token_counter(model=model, text=input_text) for input_text in inputs
        )

    # Map the model name to the actual model name
    actual_model = model

    # Create usage record for embeddings (no completion tokens)
    await create_usage_record(
        developer_id=developer_id,
        model=actual_model,
        prompt_tokens=prompt_tokens,
        completion_tokens=0,  # Embeddings don't have completion tokens
        custom_api_used=custom_api_used,
        metadata=metadata,
    )

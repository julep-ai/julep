"""
Utilities for tracking token usage and costs for LLM API calls.
"""

from typing import Any
from uuid import UUID

from beartype import beartype
from litellm.utils import ModelResponse, token_counter

from ...queries.usage.create_usage_record import create_usage_record


@beartype
def extract_provider_from_model(model: str) -> str | None:
    """
    Extract the provider from a model name.

    Args:
        model (str): The model name (e.g., "gpt-4", "claude-3-sonnet", "openai/gpt-4")

    Returns:
        str | None: The provider name (e.g., "openai", "anthropic") or None if unknown
    """
    # Handle prefixed models (e.g., "openai/gpt-4")
    if "/" in model:
        provider_prefix = model.split("/")[0].lower()
        # Map some common prefixes
        provider_mapping = {
            "openai": "openai",
            "anthropic": "anthropic",
            "google": "google",
            "meta-llama": "meta",
            "mistralai": "mistral",
            "openrouter": "openrouter",
        }
        if provider_prefix in provider_mapping:
            return provider_mapping[provider_prefix]

    # Detect based on model name patterns
    model_lower = model.lower()

    if any(
        pattern in model_lower
        for pattern in ["gpt-", "o1-", "text-davinci", "text-ada", "text-babbage", "text-curie"]
    ):
        return "openai"
    if any(pattern in model_lower for pattern in ["claude-", "claude"]):
        return "anthropic"
    if any(pattern in model_lower for pattern in ["gemini-", "palm-", "bison", "gecko"]):
        return "google"
    if any(pattern in model_lower for pattern in ["llama-", "llama2", "llama3", "meta-llama"]):
        return "meta"
    if any(pattern in model_lower for pattern in ["mistral-", "mixtral-"]):
        return "mistral"
    if any(pattern in model_lower for pattern in ["qwen-", "qwen2"]):
        return "qwen"

    return None


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
    session_id: UUID | None = None,
    execution_id: UUID | None = None,
    transition_id: UUID | None = None,
    entry_id: UUID | None = None,
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
        session_id (UUID | None): The session that generated this usage.
        execution_id (UUID | None): The task execution that generated this usage.
        transition_id (UUID | None): The specific transition step that generated this usage.
        entry_id (UUID | None): The chat entry that generated this usage.

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

    # Extract provider from model name
    provider = extract_provider_from_model(actual_model)

    # Create usage record
    # AIDEV-NOTE: 1472:: Updated to pass new context fields and provider for better tracking
    await create_usage_record(
        developer_id=developer_id,
        model=actual_model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        custom_api_used=custom_api_used,
        metadata={
            "request_id": response.id if hasattr(response, "id") else None,
            "input_messages": messages,
            "output_content": [
                choice.message.content
                for choice in response.choices
                if hasattr(choice, "message")
                and choice.message
                and hasattr(choice.message, "content")
            ]
            if response.choices
            else None,
            **metadata,
        },
        session_id=session_id,
        execution_id=execution_id,
        transition_id=transition_id,
        entry_id=entry_id,
        provider=provider,
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

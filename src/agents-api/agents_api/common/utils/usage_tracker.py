"""
Centralized usage tracking utilities for LLM API calls.
Handles both Prometheus metrics and database tracking.
"""

from typing import Any
from uuid import UUID

from beartype import beartype
from litellm.utils import ModelResponse, Choices, Message
from prometheus_client import Counter

from .usage import track_usage

# Prometheus metrics
total_tokens_per_user = Counter(
    "total_tokens_per_user",
    "Total token count per user",
    labelnames=("developer_id",),
)


@beartype
async def track_completion_usage(
    *,
    developer_id: UUID,
    model: str,
    messages: list[dict],
    response: ModelResponse,
    custom_api_used: bool = False,
    metadata: dict[str, Any] = {},
    connection_pool: Any = None,
) -> None:
    """
    Tracks usage for completion responses (both streaming and non-streaming).
    
    Args:
        developer_id: The developer ID for usage tracking
        model: The model name used for the response
        messages: The original messages sent to the model
        response: The model response
        custom_api_used: Whether a custom API key was used
        metadata: Additional metadata for tracking
        connection_pool: Connection pool for testing purposes
    """
    # Track Prometheus metrics
    if response.usage and response.usage.total_tokens > 0:
        total_tokens_per_user.labels(str(developer_id)).inc(
            amount=response.usage.total_tokens
        )

    # Track usage in database
    await track_usage(
        developer_id=developer_id,
        model=model,
        messages=messages,
        response=response,
        custom_api_used=custom_api_used,
        metadata=metadata,
        connection_pool=connection_pool,
    )


@beartype
async def track_streaming_usage(
    *,
    developer_id: UUID,
    model: str,
    messages: list[dict],
    usage_data: dict[str, Any] | None,
    collected_output: list[dict],
    response_id: str,
    custom_api_used: bool = False,
    metadata: dict[str, Any] = None,
    connection_pool: Any = None,
) -> None:
    """
    Tracks usage for streaming responses.
    
    Args:
        developer_id: The developer ID for usage tracking
        model: The model name used for the response
        messages: The original messages sent to the model
        usage_data: Usage data from the streaming response
        collected_output: The complete collected output from streaming
        response_id: The response ID
        custom_api_used: Whether a custom API key was used
        metadata: Additional metadata for tracking
        connection_pool: Connection pool for testing purposes
    """
    # Track Prometheus metrics if usage data is available
    if usage_data and usage_data.get("total_tokens", 0) > 0:
        total_tokens_per_user.labels(str(developer_id)).inc(
            amount=usage_data.get("total_tokens", 0)
        )

    # Only track usage in database if we have collected output
    if not collected_output:
        return

    # Track usage in database
    await track_usage(
        developer_id=developer_id,
        model=model,
        messages=messages,
        response=ModelResponse(
            id=response_id,
            choices=[
                Choices(
                    message=Message(
                        content=choice.get("content", ""),
                        tool_calls=choice.get("tool_calls"),
                    ),
                )
                for choice in collected_output
            ],
            usage=usage_data,
        ),
        custom_api_used=custom_api_used,
        metadata=metadata,
        connection_pool=connection_pool,
    ) 
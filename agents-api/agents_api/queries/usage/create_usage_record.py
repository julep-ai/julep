"""
This module contains functionality for creating usage records in the PostgreSQL database.
It tracks token usage and costs for LLM API calls.
"""

from typing import Any
from uuid import UUID

from beartype import beartype
from litellm import cost_per_token

from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions

# Define the raw SQL query
usage_query = """
INSERT INTO usage (
    developer_id,
    model,
    prompt_tokens,
    completion_tokens,
    cost,
    estimated,
    custom_api_used,
    metadata
)
VALUES (
    $1, -- developer_id
    $2, -- model
    $3, -- prompt_tokens
    $4, -- completion_tokens
    $5, -- cost
    $6, -- estimated
    $7, -- custom_api_used
    $8  -- metadata
)
RETURNING *;
"""


@rewrap_exceptions(common_db_exceptions("usage", ["create"]))
@query_metrics("create_usage_record")
@pg_query
@beartype
async def create_usage_record(
    *,
    developer_id: UUID,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    custom_api_used: bool = False,
    estimated: bool = False,
    metadata: dict[str, Any] = {},
) -> tuple[str, list]:
    """
    Creates a usage record to track token usage and costs.

    Parameters:
        developer_id (UUID): The unique identifier for the developer.
        model (str): The model used for the API call.
        prompt_tokens (int): Number of tokens in the prompt.
        completion_tokens (int): Number of tokens in the completion.
        custom_api_used (bool): Whether a custom API key was used.
        estimated (bool): Whether the token count is estimated.
        metadata (dict): Additional metadata about the usage.

    Returns:
        tuple[str, list]: SQL query and parameters for creating the usage record.
    """
    # Calculate cost based on token usage
    # For custom API keys, we still track usage but mark it as such
    total_cost = 0.0
    
    if not custom_api_used:
        # Calculate cost using litellm's cost_per_token function
        try:
            prompt_cost, completion_cost = cost_per_token(model, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
            total_cost = prompt_cost + completion_cost
        except Exception as e:
            estimated = True
            fallback_pricing = {
            # Meta Llama models
            'meta-llama/llama-4-scout': {'api_request': 0.08/1000, 'api_response': 0.45/1000},
            'meta-llama/llama-4-maverick': {'api_request': 0.19/1000, 'api_response': 0.85/1000},
            'meta-llama/llama-4-maverick:free': {'api_request': 0.0/1000, 'api_response': 0.0/1000},
            
            # Qwen model
            'qwen/qwen-2.5-72b-instruct': {'api_request': 0.7/1000, 'api_response': 0.7/1000},
            
            # Sao10k model
            'sao10k/l3.3-euryale-70b': {'api_request': 0.7/1000, 'api_response': 0.8/1000},
            'sao10k/l3.1-euryale-70b': {'api_request': 0.7/1000, 'api_response': 0.8/1000}
            }
        
            if model in fallback_pricing:
                total_cost = fallback_pricing[model]['api_request'] * prompt_tokens + fallback_pricing[model]['api_response'] * completion_tokens
            else:
                print(f"No fallback pricing found for model {model}")

    params = [
        developer_id,
        model,
        prompt_tokens,
        completion_tokens,
        total_cost,
        estimated,
        custom_api_used,
        metadata or {},
    ]

    return (
        usage_query,
        params,
    ) 
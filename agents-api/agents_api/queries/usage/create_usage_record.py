"""
This module contains functionality for creating usage records in the PostgreSQL database.
It tracks token usage and costs for LLM API calls.
"""

from typing import Any
from uuid import UUID

from beartype import beartype
from litellm import cost_per_token, model_cost

from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions

FALLBACK_PRICING = {
    # Meta Llama models
    "meta-llama/llama-4-scout": {
        "api_request": 0.08 / 1000000,
        "api_response": 0.45 / 1000000,
    },
    "meta-llama/llama-4-maverick": {
        "api_request": 0.19 / 1000000,
        "api_response": 0.85 / 1000000,
    },
    "meta-llama/llama-4-maverick:free": {
        "api_request": 0.0 / 1000000,
        "api_response": 0.0 / 1000000,
    },
    # Qwen model
    "qwen/qwen-2.5-72b-instruct": {
        "api_request": 0.7 / 1000000,
        "api_response": 0.7 / 1000000,
    },
    # Sao10k model
    "sao10k/l3.3-euryale-70b": {
        "api_request": 0.7 / 1000000,
        "api_response": 0.8 / 1000000,
    },
    "sao10k/l3.1-euryale-70b": {
        "api_request": 0.7 / 1000000,
        "api_response": 0.8 / 1000000,
    },
    # eva-unit-01 model
    "openrouter/eva-unit-01/eva-llama-3.33-70b": {
        "api_request": 4 / 1000000,
        "api_response": 6 / 1000000,
    },
    "openrouter/eva-unit-01/eva-qwen-2.5-72b": {
        "api_request": 0.9 / 1000000,
        "api_response": 1.2 / 1000000,
    },
    # mistral-large-2411 model
    "openrouter/mistralai/mistral-large-2411": {
        "api_request": 2 / 1000000,
        "api_response": 6 / 1000000,
    },
}

# Calculate average of non-zero input costs
input_costs_litellm = [
    model_cost[model].get("input_cost_per_token", 0)
    for model in model_cost
    if model_cost[model].get("input_cost_per_token", 0) > 0
]
input_costs_fallback = [
    pricing["api_request"]
    for pricing in FALLBACK_PRICING.values()
    if pricing["api_request"] > 0
]
combined_input_costs = input_costs_litellm + input_costs_fallback
AVG_INPUT_COST_PER_TOKEN = (
    sum(combined_input_costs) / len(combined_input_costs) if combined_input_costs else 0
)

# Calculate average of non-zero output costs
output_costs_litellm = [
    model_cost[model].get("output_cost_per_token", 0)
    for model in model_cost
    if model_cost[model].get("output_cost_per_token", 0) > 0
]
output_costs_fallback = [
    pricing["api_response"]
    for pricing in FALLBACK_PRICING.values()
    if pricing["api_response"] > 0
]
combined_output_costs = output_costs_litellm + output_costs_fallback
AVG_OUTPUT_COST_PER_TOKEN = (
    sum(combined_output_costs) / len(combined_output_costs) if combined_output_costs else 0
)

# AIDEV-NOTE: 1472:: Updated query to include new reference fields and provider for better tracking
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
    metadata,
    session_id,
    execution_id,
    transition_id,
    entry_id,
    provider
)
VALUES (
    $1, -- developer_id
    $2, -- model
    $3, -- prompt_tokens
    $4, -- completion_tokens
    $5, -- cost
    $6, -- estimated
    $7, -- custom_api_used
    $8, -- metadata
    $9, -- session_id
    $10, -- execution_id
    $11, -- transition_id
    $12, -- entry_id
    $13  -- provider
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
    metadata: dict[str, Any] | None = None,
    session_id: UUID | None = None,
    execution_id: UUID | None = None,
    transition_id: UUID | None = None,
    entry_id: UUID | None = None,
    provider: str | None = None,
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
        metadata (dict | None): Additional metadata about the usage.
        session_id (UUID | None): The session that generated this usage.
        execution_id (UUID | None): The task execution that generated this usage.
        transition_id (UUID | None): The specific transition step that generated this usage.
        entry_id (UUID | None): The chat entry that generated this usage.
        provider (str | None): The actual LLM provider used (e.g., openai, anthropic, google).

    Returns:
        tuple[str, list]: SQL query and parameters for creating the usage record.
    """
    # Calculate cost based on token usage
    # For custom API keys, we still track usage but mark it as such
    total_cost = 0.0

    try:
        prompt_cost, completion_cost = cost_per_token(
            model, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
        )
        total_cost = prompt_cost + completion_cost
    except Exception:
        estimated = True

        if model in FALLBACK_PRICING:
            total_cost = (
                FALLBACK_PRICING[model]["api_request"] * prompt_tokens
                + FALLBACK_PRICING[model]["api_response"] * completion_tokens
            )
        else:
            total_cost = (
                AVG_INPUT_COST_PER_TOKEN * prompt_tokens
                + AVG_OUTPUT_COST_PER_TOKEN * completion_tokens
            )
            print(f"No fallback pricing found for model {model}, using avg costs: {total_cost}")

    # AIDEV-NOTE: 1472:: Updated to include new reference fields and provider in params list
    params = [
        developer_id,
        model,
        prompt_tokens,
        completion_tokens,
        total_cost,
        estimated,
        custom_api_used,
        metadata or {},
        session_id,
        execution_id,
        transition_id,
        entry_id,
        provider,
    ]

    return (
        usage_query,
        params,
    )

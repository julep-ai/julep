"""
Tests for usage tracking functionality.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from agents_api.clients.pg import create_db_pool
from agents_api.common.utils.usage import track_embedding_usage, track_usage
from agents_api.queries.usage.create_usage_record import (
    AVG_INPUT_COST_PER_TOKEN,
    AVG_OUTPUT_COST_PER_TOKEN,
    create_usage_record,
)
from litellm import cost_per_token
from litellm.utils import Message, ModelResponse, Usage, token_counter
import pytest

from .fixtures import pg_dsn, test_developer_id


@pytest.mark.asyncio
async def test_query_create_usage_record_creates_a_record_with_correct_parameters(dsn=pg_dsn, developer_id=test_developer_id) -> None:
    """query: create_usage_record creates a record with correct parameters"""
    pool = await create_db_pool(dsn=dsn)
    response = await create_usage_record(
        developer_id=developer_id,
        model="gpt-4o-mini",
        prompt_tokens=100,
        completion_tokens=100,
        connection_pool=pool,
    )
    assert len(response) == 1
    record = response[0]
    assert record["developer_id"] == developer_id
    assert record["model"] == "gpt-4o-mini"
    assert record["prompt_tokens"] == 100
    assert record["completion_tokens"] == 100
    assert record["cost"] == Decimal("0.000075")
    assert record["estimated"] is False
    assert record["custom_api_used"] is False
    assert record["metadata"] == {}
    assert isinstance(record["created_at"], datetime)


@pytest.mark.asyncio
async def test_query_create_usage_record_handles_different_model_names_correctly(dsn=pg_dsn, developer_id=test_developer_id) -> None:
    """query: create_usage_record handles different model names correctly"""
    pool = await create_db_pool(dsn=dsn)
    models = [
        "gpt-4o-mini",
        "claude-3.5-sonnet",
        "claude-3.7-sonnet",
        "claude-3-haiku",
        "deepseek-chat",
        "gemini-1.5-pro",
        "gemini-1.5-pro-latest",
        "gemini-2.0-flash",
        "gemini-2.5-pro-preview-03-25",
        "mistral-large-2411",
        "meta-llama/llama-4-scout",
        "meta-llama/llama-4-maverick",
        "meta-llama/llama-4-maverick:free",
        "qwen/qwen-2.5-72b-instruct",
        "sao10k/l3.3-euryale-70b",
        "sao10k/l3.1-euryale-70b",
    ]
    for model in models:
        response = await create_usage_record(
            developer_id=developer_id,
            model=model,
            prompt_tokens=100,
            completion_tokens=100,
            connection_pool=pool,
        )
        assert len(response) == 1
        record = response[0]
        assert record["model"] == model


@pytest.mark.asyncio
async def test_query_create_usage_record_properly_calculates_costs(dsn=pg_dsn, developer_id=test_developer_id) -> None:
    """query: create_usage_record properly calculates costs"""
    pool = await create_db_pool(dsn=dsn)
    response = await create_usage_record(
        developer_id=developer_id,
        model="gpt-4o-mini",
        prompt_tokens=2041,
        completion_tokens=34198,
        connection_pool=pool,
    )

    input_cost, completion_cost = cost_per_token(
        "gpt-4o-mini", prompt_tokens=2041, completion_tokens=34198
    )
    cost = input_cost + completion_cost
    cost = Decimal(str(cost)).quantize(Decimal("0.000001"))

    assert len(response) == 1
    record = response[0]
    assert record["cost"] == cost


@pytest.mark.asyncio
async def test_query_create_usage_record_with_custom_api_key(dsn=pg_dsn, developer_id=test_developer_id) -> None:
    """query: create_usage_record with custom API key"""
    pool = await create_db_pool(dsn=dsn)
    response = await create_usage_record(
        developer_id=developer_id,
        model="gpt-4o-mini",
        prompt_tokens=100,
        completion_tokens=100,
        custom_api_used=True,
        connection_pool=pool,
    )

    input_cost, completion_cost = cost_per_token(
        "gpt-4o-mini", prompt_tokens=100, completion_tokens=100
    )
    cost = input_cost + completion_cost
    cost = Decimal(str(cost)).quantize(Decimal("0.000001"))

    assert len(response) == 1
    record = response[0]
    assert record["custom_api_used"] is True
    assert record["cost"] == cost


@pytest.mark.asyncio
async def test_query_create_usage_record_with_fallback_pricing(dsn=pg_dsn, developer_id=test_developer_id) -> None:
    """query: create_usage_record with fallback pricing"""
    pool = await create_db_pool(dsn=dsn)
    response = await create_usage_record(
        developer_id=developer_id,
        model="meta-llama/llama-4-maverick:free",
        prompt_tokens=100,
        completion_tokens=100,
        connection_pool=pool,
    )

    assert len(response) == 1
    record = response[0]
    assert record["cost"] == Decimal("0.000000")
    assert record["estimated"] is True


@pytest.mark.asyncio
async def test_query_create_usage_record_with_fallback_pricing_with_model_not_in_fallback_pricing(dsn=pg_dsn, developer_id=test_developer_id) -> None:
    """query: create_usage_record with fallback pricing with model not in fallback pricing"""
    pool = await create_db_pool(dsn=dsn)

    with patch("builtins.print") as mock_print:
        unknown_model = "unknown-model-name"
        response = await create_usage_record(
            developer_id=developer_id,
            model=unknown_model,
            prompt_tokens=100,
            completion_tokens=100,
            connection_pool=pool,
        )
    actual_call = mock_print.call_args_list[-1].args[0]
    total_cost = AVG_INPUT_COST_PER_TOKEN * 100 + AVG_OUTPUT_COST_PER_TOKEN * 100

    expected_call = (
        f"No fallback pricing found for model {unknown_model}, using avg costs: {total_cost}"
    )

    assert len(response) == 1
    record = response[0]
    assert record["cost"] == Decimal(str(total_cost)).quantize(Decimal("0.000001"))
    assert record["estimated"] is True
    assert expected_call == actual_call


@pytest.mark.asyncio
async def test_utils_track_usage_with_response_usage_available(developer_id=test_developer_id) -> None:
    """utils: track_usage with response.usage available"""
    with patch("agents_api.common.utils.usage.create_usage_record") as mock_create_usage_record:
        response = ModelResponse(
            usage=Usage(
                prompt_tokens=100,
                completion_tokens=100,
            ),
        )

        await track_usage(
            developer_id=developer_id,
            model="gpt-4o-mini",
            messages=[],
            response=response,
        )
        call_args = mock_create_usage_record.call_args[1]
        assert call_args["prompt_tokens"] == 100
        assert call_args["completion_tokens"] == 100


@pytest.mark.asyncio
async def test_utils_track_usage_without_response_usage(developer_id=test_developer_id) -> None:
    """utils: track_usage without response.usage"""
    with patch("agents_api.common.utils.usage.create_usage_record") as mock_create_usage_record:
        response = ModelResponse(
            usage=None,
            choices=[
                {
                    "finish_reason": "stop",
                    "index": 0,
                    "message": Message(content="Hello, world!", role="assistant"),
                }
            ],
        )
        response.usage = None
        messages = [{"role": "user", "content": "Hello, world!"}]

        prompt_tokens = token_counter(model="gpt-4o-mini", messages=messages)
        completion_tokens = token_counter(
            model="gpt-4o-mini",
            messages=[{"content": choice.message.content} for choice in response.choices],
        )

        await track_usage(
            developer_id=developer_id,
            model="gpt-4o-mini",
            messages=messages,
            response=response,
        )

        call_args = mock_create_usage_record.call_args[1]
        assert call_args["prompt_tokens"] == prompt_tokens
        assert call_args["completion_tokens"] == completion_tokens


@pytest.mark.asyncio
async def test_utils_track_embedding_usage_with_response_usage(developer_id=test_developer_id) -> None:
    """utils: track_embedding_usage with response.usage"""
    with patch("agents_api.common.utils.usage.create_usage_record") as mock_create_usage_record:
        response = ModelResponse(
            usage=Usage(
                prompt_tokens=150,
                completion_tokens=0,
            ),
        )

        inputs = ["This is a test input for embedding"]

        await track_embedding_usage(
            developer_id=developer_id,
            model="text-embedding-3-large",
            inputs=inputs,
            response=response,
        )

        call_args = mock_create_usage_record.call_args[1]
        assert call_args["prompt_tokens"] == 150
        assert call_args["completion_tokens"] == 0
        assert call_args["model"] == "text-embedding-3-large"


@pytest.mark.asyncio
async def test_utils_track_embedding_usage_without_response_usage(developer_id=test_developer_id) -> None:
    """utils: track_embedding_usage without response.usage"""
    with patch("agents_api.common.utils.usage.create_usage_record") as mock_create_usage_record:
        response = ModelResponse()
        response.usage = None

        inputs = ["First test input", "Second test input"]

        # Calculate expected tokens manually
        expected_tokens = sum(
            token_counter(model="text-embedding-3-large", text=input_text)
            for input_text in inputs
        )

        await track_embedding_usage(
            developer_id=developer_id,
            model="text-embedding-3-large",
            inputs=inputs,
            response=response,
        )

        call_args = mock_create_usage_record.call_args[1]
        assert call_args["prompt_tokens"] == expected_tokens
        assert call_args["completion_tokens"] == 0
        assert call_args["model"] == "text-embedding-3-large"

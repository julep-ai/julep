"""
Tests for the usage cost tracking functionality.
"""

import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from agents_api.clients.pg import create_db_pool
from agents_api.queries.developers.create_developer import create_developer
from agents_api.queries.usage.create_usage_record import create_usage_record
from agents_api.queries.usage.get_user_cost import get_usage_cost
from fastapi import HTTPException
from uuid_extensions import uuid7
from ward import test

from .fixtures import pg_dsn, test_developer_id


@test("query: get_usage_cost returns the correct cost when records exist")
async def _(dsn=pg_dsn, developer_id=test_developer_id) -> None:
    """Test that get_usage_cost returns the correct cost for a developer with usage records."""
    pool = await create_db_pool(dsn=dsn)

    # Create some usage records for the developer
    record1 = await create_usage_record(
        developer_id=developer_id,
        model="gpt-4o-mini",
        prompt_tokens=1000,
        completion_tokens=2000,
        connection_pool=pool,
    )

    record2 = await create_usage_record(
        developer_id=developer_id,
        model="gpt-4o-mini",
        prompt_tokens=500,
        completion_tokens=1500,
        connection_pool=pool,
    )

    # Calculate expected cost
    expected_cost = record1[0]["cost"] + record2[0]["cost"]

    # Force the continuous aggregate to refresh
    await pool.execute("CALL refresh_continuous_aggregate('usage_cost_monthly', NULL, NULL)")

    # Give a small delay for the view to update
    await asyncio.sleep(0.1)

    # Get the usage cost
    cost_record = await get_usage_cost(developer_id=developer_id, connection_pool=pool)

    # Verify the record
    assert cost_record is not None, "Should have a cost record"
    assert cost_record["developer_id"] == developer_id
    assert "cost" in cost_record, "Should have a cost field"
    assert isinstance(cost_record["cost"], Decimal), "Cost should be a Decimal"
    assert cost_record["cost"] == expected_cost, (
        f"Cost should be {expected_cost}, got {cost_record['cost']}"
    )
    assert "month" in cost_record, "Should have a month field"
    assert isinstance(cost_record["month"], datetime), "Month should be a datetime"


@test("query: get_usage_cost returns correct results for custom API usage")
async def _(dsn=pg_dsn) -> None:
    """Test that get_usage_cost only includes non-custom API usage in the cost calculation."""
    pool = await create_db_pool(dsn=dsn)

    # Create a new developer for this test
    dev_id = uuid7()
    email = f"test-{dev_id}@example.com"
    await create_developer(
        email=email,
        active=True,
        tags=["test"],
        settings={},
        developer_id=dev_id,
        connection_pool=pool,
    )

    # Create usage records with custom API
    await create_usage_record(
        developer_id=dev_id,
        model="gpt-4o-mini",
        prompt_tokens=1000,
        completion_tokens=2000,
        custom_api_used=True,  # This shouldn't be counted in the cost
        connection_pool=pool,
    )

    # Create usage records without custom API
    non_custom_cost = await create_usage_record(
        developer_id=dev_id,
        model="gpt-4o-mini",
        prompt_tokens=1000,
        completion_tokens=2000,
        custom_api_used=False,  # This should be counted
        connection_pool=pool,
    )

    # Calculate what the expected cost should be
    expected_cost = non_custom_cost[0]["cost"]

    # Force the continuous aggregate to refresh
    await pool.execute("CALL refresh_continuous_aggregate('usage_cost_monthly', NULL, NULL)")

    # Give a small delay for the view to update
    await asyncio.sleep(0.1)

    # Get the usage cost
    cost_record = await get_usage_cost(developer_id=dev_id, connection_pool=pool)

    # Verify the record
    assert cost_record is not None, "Should have a cost record"
    assert cost_record["developer_id"] == dev_id
    assert cost_record["cost"] == expected_cost, (
        f"Cost should match expected: {expected_cost} but got {cost_record['cost']}"
    )


@test("query: get_usage_cost returns None when no usage records exist")
async def _(dsn=pg_dsn) -> None:
    """Test that get_usage_cost returns None when no usage records exist for a developer."""
    pool = await create_db_pool(dsn=dsn)

    # Create a new developer without any usage records
    dev_id = uuid7()
    email = f"test-{dev_id}@example.com"
    await create_developer(
        email=email,
        active=True,
        tags=["test"],
        settings={},
        developer_id=dev_id,
        connection_pool=pool,
    )

    # Get the usage cost - should return None or raise 404
    try:
        cost_record = await get_usage_cost(developer_id=dev_id, connection_pool=pool)
        assert cost_record is None, "Should not have a cost record for developer with no usage"
    except HTTPException as ex:
        # Accept either None or a 404 error
        assert ex.status_code == 404, f"Expected 404 error, got {ex.status_code}"
        assert "Usage not found" in ex.detail, f"Unexpected error detail: {ex.detail}"


@test("query: get_usage_cost handles inactive developers correctly")
async def _(dsn=pg_dsn) -> None:
    """Test that get_usage_cost correctly handles inactive developers."""
    pool = await create_db_pool(dsn=dsn)

    # Create a new inactive developer
    dev_id = uuid7()
    email = f"test-{dev_id}@example.com"
    await create_developer(
        email=email,
        active=False,  # Developer is inactive
        tags=["test"],
        settings={},
        developer_id=dev_id,
        connection_pool=pool,
    )

    # Create usage records for the inactive developer
    record = await create_usage_record(
        developer_id=dev_id,
        model="gpt-4o-mini",
        prompt_tokens=1000,
        completion_tokens=2000,
        connection_pool=pool,
    )

    # Calculate expected cost
    expected_cost = record[0]["cost"]

    # Force the continuous aggregate to refresh
    await pool.execute("CALL refresh_continuous_aggregate('usage_cost_monthly', NULL, NULL)")

    # Give a small delay for the view to update
    await asyncio.sleep(0.1)

    # Get the usage cost
    cost_record = await get_usage_cost(developer_id=dev_id, connection_pool=pool)

    # Verify the record
    assert cost_record is not None, "Should have a cost record even for inactive developers"
    assert cost_record["developer_id"] == dev_id
    assert cost_record["active"] is False, "Developer should be marked as inactive"
    assert cost_record["cost"] == expected_cost, (
        f"Cost should be {expected_cost}, got {cost_record['cost']}"
    )


@test("query: get_usage_cost sorts by month correctly and returns the most recent")
async def _(dsn=pg_dsn) -> None:
    """Test that get_usage_cost returns the most recent month's cost when multiple months exist."""
    pool = await create_db_pool(dsn=dsn)

    # Create a new developer for this test
    dev_id = uuid7()
    email = f"test-{dev_id}@example.com"
    await create_developer(
        email=email,
        active=True,
        tags=["test"],
        settings={},
        developer_id=dev_id,
        connection_pool=pool,
    )

    # Create usage records for different months - using timezone-aware datetimes
    now = datetime.now(UTC)
    current_month = datetime(now.year, now.month, 1, tzinfo=UTC)
    middle_month = current_month - timedelta(days=30)
    oldest_month = current_month - timedelta(days=60)

    # Create a cost for the current month
    current_cost_record = await create_usage_record(
        developer_id=dev_id,
        model="gpt-4o-mini",
        prompt_tokens=600,
        completion_tokens=1200,
        connection_pool=pool,
    )
    current_cost = current_cost_record[0]["cost"]

    # Create a cost for the middle month (insert with timestamp)
    await pool.execute(
        """
        INSERT INTO usage (
            developer_id, model, prompt_tokens, completion_tokens, cost, created_at
        ) VALUES ($1, 'gpt-4o-mini', 400, 800, $2, $3)
        """,
        dev_id,
        Decimal("0.004000"),
        middle_month,
    )

    # Create a cost for the oldest month
    await pool.execute(
        """
        INSERT INTO usage (
            developer_id, model, prompt_tokens, completion_tokens, cost, created_at
        ) VALUES ($1, 'gpt-4o-mini', 200, 400, $2, $3)
        """,
        dev_id,
        Decimal("0.002000"),
        oldest_month,
    )

    # Force the continuous aggregate to refresh
    await pool.execute("CALL refresh_continuous_aggregate('usage_cost_monthly', NULL, NULL)")

    # Give a small delay for the view to update
    await asyncio.sleep(0.1)

    # Get the usage cost
    cost_record = await get_usage_cost(developer_id=dev_id, connection_pool=pool)

    # We expect the most recent month to be returned
    assert cost_record is not None, "Should have a cost record"
    assert cost_record["developer_id"] == dev_id

    # The month in the record should be close to the current month's date
    # Ensure both datetimes are timezone-aware
    record_month = cost_record["month"]
    month_diff = abs((record_month - current_month).total_seconds())
    assert month_diff < 86400, "Month should be near the start of the current month"

    # The cost should match only the current month
    assert cost_record["cost"] == current_cost, (
        f"Cost should match current month's usage only: expected {current_cost}, got {cost_record['cost']}"
    )

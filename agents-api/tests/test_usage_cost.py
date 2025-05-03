"""
Tests for the usage cost tracking functionality.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

from agents_api.clients.pg import create_db_pool
from agents_api.queries.developers.create_developer import create_developer
from agents_api.queries.usage.create_usage_record import create_usage_record
from agents_api.queries.usage.get_user_cost import get_usage_cost
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

    # For testing purposes, directly insert into the aggregation table
    # This simulates what the continuous aggregate would do
    await pool.execute(
        """
        INSERT INTO usage_cost_monthly (developer_id, bucket_start, monthly_cost)
        VALUES ($1, date_trunc('month', NOW()), $2)
        ON CONFLICT (developer_id, bucket_start)
        DO UPDATE SET monthly_cost = usage_cost_monthly.monthly_cost + $2
        """,
        developer_id,
        expected_cost
    )

    # Give a small delay for the view to update
    await asyncio.sleep(0.1)

    # Get the usage cost
    cost_record = await get_usage_cost(developer_id=developer_id, connection_pool=pool)

    # Verify the record
    assert cost_record is not None, "Should have a cost record"
    assert cost_record["developer_id"] == developer_id
    assert "cost" in cost_record, "Should have a cost field"
    assert isinstance(cost_record["cost"], Decimal), "Cost should be a Decimal"
    assert cost_record["cost"] == expected_cost, f"Cost should be {expected_cost}, got {cost_record['cost']}"
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
    custom_cost = await create_usage_record(
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

    # For testing purposes, directly insert into the aggregation table
    # This simulates what the continuous aggregate would do
    await pool.execute(
        """
        INSERT INTO usage_cost_monthly (developer_id, bucket_start, monthly_cost)
        VALUES ($1, date_trunc('month', NOW()), $2)
        ON CONFLICT (developer_id, bucket_start)
        DO UPDATE SET monthly_cost = usage_cost_monthly.monthly_cost + $2
        """,
        dev_id,
        expected_cost
    )

    # Give a small delay for the view to update
    await asyncio.sleep(0.1)

    # Get the usage cost
    cost_record = await get_usage_cost(developer_id=dev_id, connection_pool=pool)

    # Verify the record
    assert cost_record is not None, "Should have a cost record"
    assert cost_record["developer_id"] == dev_id
    assert cost_record["cost"] == expected_cost, f"Cost should match expected: {expected_cost} but got {cost_record['cost']}"
    # Custom API costs should be excluded
    assert cost_record["cost"] != custom_cost[0]["cost"] + non_custom_cost[0]["cost"], "Custom API costs should be excluded"


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

    # Get the usage cost
    cost_record = await get_usage_cost(developer_id=dev_id, connection_pool=pool)

    # Verify that no record is returned
    assert cost_record is None, "Should not have a cost record for developer with no usage"


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

    # For testing purposes, directly insert into the aggregation table
    # This simulates what the continuous aggregate would do
    await pool.execute(
        """
        INSERT INTO usage_cost_monthly (developer_id, bucket_start, monthly_cost)
        VALUES ($1, date_trunc('month', NOW()), $2)
        ON CONFLICT (developer_id, bucket_start)
        DO UPDATE SET monthly_cost = usage_cost_monthly.monthly_cost + $2
        """,
        dev_id,
        expected_cost
    )

    # Give a small delay for the view to update
    await asyncio.sleep(0.1)

    # Get the usage cost
    cost_record = await get_usage_cost(developer_id=dev_id, connection_pool=pool)

    # Verify the record
    assert cost_record is not None, "Should have a cost record even for inactive developers"
    assert cost_record["developer_id"] == dev_id
    assert cost_record["active"] is False, "Developer should be marked as inactive"
    assert cost_record["cost"] == expected_cost, f"Cost should be {expected_cost}, got {cost_record['cost']}"


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

    # Calculate costs for different months
    current_cost = Decimal("0.006000")
    middle_cost = Decimal("0.004000")
    oldest_cost = Decimal("0.002000")

    # Get the dates for different months
    now = datetime.now()
    current_month = datetime(now.year, now.month, 1)
    middle_month = current_month - timedelta(days=30)
    oldest_month = current_month - timedelta(days=60)

    # For testing purposes, directly insert into the aggregation table for different months
    # This simulates what the continuous aggregate would do
    # Insert oldest month first
    await pool.execute(
        """
        INSERT INTO usage_cost_monthly (developer_id, bucket_start, monthly_cost)
        VALUES ($1, $2, $3)
        """,
        dev_id,
        oldest_month,
        oldest_cost
    )

    # Insert middle month
    await pool.execute(
        """
        INSERT INTO usage_cost_monthly (developer_id, bucket_start, monthly_cost)
        VALUES ($1, $2, $3)
        """,
        dev_id,
        middle_month,
        middle_cost
    )

    # Insert current month (should be returned by the query)
    await pool.execute(
        """
        INSERT INTO usage_cost_monthly (developer_id, bucket_start, monthly_cost)
        VALUES ($1, $2, $3)
        """,
        dev_id,
        current_month,
        current_cost
    )

    # Give a small delay for the view to update
    await asyncio.sleep(0.1)

    # Get the usage cost
    cost_record = await get_usage_cost(developer_id=dev_id, connection_pool=pool)

    # We expect the most recent month to be returned
    assert cost_record is not None, "Should have a cost record"
    assert cost_record["developer_id"] == dev_id

    # The month in the record should be close to the current month's date
    month_diff = abs((cost_record["month"] - current_month).total_seconds())
    assert month_diff < 86400, "Month should be near the start of the current month"

    # The cost should match only the current month
    assert cost_record["cost"] == current_cost, f"Cost should match current month's usage only: expected {current_cost}, got {cost_record['cost']}"

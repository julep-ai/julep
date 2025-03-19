"""Tests for secrets queries."""

import os
import uuid
from typing import Any

import pytest
from agents_api.app import app
from agents_api.clients.pg import get_db_connection
from agents_api.queries.secrets import (
    SecretInput,
    create_secret,
    delete_secret,
    get_secret,
    get_secret_by_name,
    list_secrets,
    patch_secret,
    update_secret,
)
from fastapi.testclient import TestClient
from psycopg import AsyncConnection
from pytest import FixtureRequest, fixture


@fixture
async def test_conn(request: FixtureRequest) -> AsyncConnection[dict[str, Any]]:
    """Get a test database connection."""
    pg_dsn = os.environ.get("PG_DSN")
    if not pg_dsn:
        pytest.skip("No PG_DSN environment variable")

    conn = await get_db_connection(pg_dsn)
    request.addfinalizer(lambda: conn.close())
    return conn


@fixture
def test_client() -> TestClient:
    """Get a test client for the FastAPI app."""
    return TestClient(app)


@fixture
def mock_developer_id() -> uuid.UUID:
    """Get a mock developer ID for testing."""
    return uuid.UUID("00000000-0000-0000-0000-000000000001")


@fixture
def mock_agent_id() -> uuid.UUID:
    """Get a mock agent ID for testing."""
    return uuid.UUID("00000000-0000-0000-0000-000000000002")


@pytest.mark.skip("Integration test, only run manually")
async def test_create_and_get_secret(test_conn, mock_developer_id):
    """Test creating and retrieving a secret."""
    # Create a secret
    secret_input = SecretInput(
        name="TEST_API_KEY",
        value="test-secret-value",
        description="Test API Key for integration testing",
        metadata={"purpose": "testing"},
    )

    result = await create_secret(test_conn, mock_developer_id, secret_input)

    # Verify the result
    assert result.name == "TEST_API_KEY"
    assert result.description == "Test API Key for integration testing"
    assert result.metadata == {"purpose": "testing"}
    assert result.developer_id == mock_developer_id
    assert result.agent_id is None

    # Get the secret by ID
    retrieved = await get_secret(test_conn, result.id, mock_developer_id)
    assert retrieved is not None
    assert retrieved.name == "TEST_API_KEY"
    assert retrieved.description == "Test API Key for integration testing"

    # Get the secret value by name
    secret_value = await get_secret_by_name(test_conn, "TEST_API_KEY", mock_developer_id)
    assert secret_value is not None
    hashed_value, metadata = secret_value
    assert isinstance(hashed_value, str)
    assert metadata == {"purpose": "testing"}

    # Clean up
    await delete_secret(test_conn, result.id, mock_developer_id)


@pytest.mark.skip("Integration test, only run manually")
async def test_list_secrets(test_conn, mock_developer_id):
    """Test listing secrets."""
    # Create a few secrets
    secrets = []
    for i in range(3):
        secret_input = SecretInput(
            name=f"TEST_KEY_{i}",
            value=f"test-value-{i}",
            description=f"Test key {i}",
        )
        result = await create_secret(test_conn, mock_developer_id, secret_input)
        secrets.append(result)

    # List the secrets
    listed = await list_secrets(test_conn, mock_developer_id)

    # Verify the list
    assert len(listed) >= 3  # Could be more if previous tests left secrets

    # Find our test secrets in the list
    test_secrets = [s for s in listed if s.name.startswith("TEST_KEY_")]
    assert len(test_secrets) == 3

    # Clean up
    for secret in secrets:
        await delete_secret(test_conn, secret.id, mock_developer_id)


@pytest.mark.skip("Integration test, only run manually")
async def test_update_and_patch_secret(test_conn, mock_developer_id, mock_agent_id):
    """Test updating and patching a secret."""
    # Create a secret
    secret_input = SecretInput(
        name="UPDATE_TEST_KEY",
        value="original-value",
        description="Original description",
    )
    result = await create_secret(test_conn, mock_developer_id, secret_input)

    # Update the secret
    updated = await update_secret(
        test_conn,
        result.id,
        mock_developer_id,
        SecretInput(
            name="UPDATE_TEST_KEY",
            value="updated-value",
            description="Updated description",
            agent_id=mock_agent_id,
        ),
    )

    # Verify the update
    assert updated is not None
    assert updated.name == "UPDATE_TEST_KEY"
    assert updated.description == "Updated description"
    assert updated.agent_id == mock_agent_id

    # Patch the secret
    patched = await patch_secret(
        test_conn,
        updated.id,
        mock_developer_id,
        {"description": "Patched description"},
    )

    # Verify the patch
    assert patched is not None
    assert patched.name == "UPDATE_TEST_KEY"
    assert patched.description == "Patched description"
    assert patched.agent_id == mock_agent_id

    # Clean up
    await delete_secret(test_conn, result.id, mock_developer_id)

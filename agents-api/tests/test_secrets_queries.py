"""Tests for secrets queries."""

import os
from uuid import UUID

from agents_api.clients.pg import create_db_pool
from agents_api.queries.secrets import (
    PatchSecretInput,
    SecretInput,
    create_secret,
    delete_secret,
    get_secret,
    get_secret_by_name,
    list_secrets,
    patch_secret,
    update_secret,
)
from ward import fixture, skip, test

# Create fixtures


@fixture(scope="test")
def pg_dsn():
    pg_dsn = os.environ.get("PG_DSN")
    if not pg_dsn:
        skip("No PG_DSN environment variable")

    return pg_dsn


@fixture(scope="test")
def mock_developer_id() -> UUID:
    """Get a mock developer ID for testing."""
    return UUID("00000000-0000-0000-0000-000000000001")


@fixture(scope="test")
def mock_agent_id() -> UUID:
    """Get a mock agent ID for testing."""
    return UUID("00000000-0000-0000-0000-000000000002")


@test("Create and retrieve a secret", tags=["integration"])
@skip("Integration test, only run manually")
async def _(dsn=pg_dsn, developer_id=mock_developer_id):
    """Test creating and retrieving a secret."""
    pool = await create_db_pool(dsn=dsn)

    # Create a secret
    secret_input = SecretInput(
        name="TEST_API_KEY",
        value="test-secret-value",
        description="Test API Key for integration testing",
        metadata={"purpose": "testing"},
    )

    result = await create_secret(
        conn=pool,
        developer_id=developer_id,
        input=secret_input,
    )

    # Verify the result
    assert result.name == "TEST_API_KEY"
    assert result.description == "Test API Key for integration testing"
    assert result.metadata == {"purpose": "testing"}
    assert result.developer_id == developer_id
    assert result.agent_id is None

    # Get the secret by ID
    retrieved = await get_secret(
        conn=pool,
        secret_id=result.id,
        developer_id=developer_id,
    )
    assert retrieved is not None
    assert retrieved.name == "TEST_API_KEY"
    assert retrieved.description == "Test API Key for integration testing"

    # Get the secret value by name
    secret_value = await get_secret_by_name(
        conn=pool,
        name="TEST_API_KEY",
        developer_id=developer_id,
    )
    assert secret_value is not None
    hashed_value, metadata = secret_value
    assert isinstance(hashed_value, str)
    assert metadata == {"purpose": "testing"}

    # Clean up
    await delete_secret(
        conn=pool,
        secret_id=result.id,
        developer_id=developer_id,
    )

    await pool.close()


@test("List secrets", tags=["integration"])
@skip("Integration test, only run manually")
async def _(dsn=pg_dsn, developer_id=mock_developer_id):
    """Test listing secrets."""
    pool = await create_db_pool(dsn=dsn)

    # Create a few secrets
    secrets = []
    for i in range(3):
        secret_input = SecretInput(
            name=f"TEST_KEY_{i}",
            value=f"test-value-{i}",
            description=f"Test key {i}",
        )
        result = await create_secret(
            conn=pool,
            developer_id=developer_id,
            input=secret_input,
        )
        secrets.append(result)

    # List the secrets
    listed = await list_secrets(
        conn=pool,
        developer_id=developer_id,
    )

    # Verify the list
    assert len(listed) >= 3  # Could be more if previous tests left secrets

    # Find our test secrets in the list
    test_secrets = [s for s in listed if s.name.startswith("TEST_KEY_")]
    assert len(test_secrets) == 3

    # Clean up
    for secret in secrets:
        await delete_secret(
            conn=pool,
            secret_id=secret.id,
            developer_id=developer_id,
        )

    await pool.close()


@test("Update and patch a secret", tags=["integration"])
@skip("Integration test, only run manually")
async def _(dsn=pg_dsn, developer_id=mock_developer_id, agent_id=mock_agent_id):
    """Test updating and patching a secret."""
    pool = await create_db_pool(dsn=dsn)

    # Create a secret
    secret_input = SecretInput(
        name="UPDATE_TEST_KEY",
        value="original-value",
        description="Original description",
    )
    result = await create_secret(
        conn=pool,
        developer_id=developer_id,
        input=secret_input,
    )

    # Update the secret
    updated = await update_secret(
        conn=pool,
        secret_id=result.id,
        developer_id=developer_id,
        input=SecretInput(
            name="UPDATE_TEST_KEY",
            value="updated-value",
            description="Updated description",
            agent_id=agent_id,
        ),
    )

    # Verify the update
    assert updated is not None
    assert updated.name == "UPDATE_TEST_KEY"
    assert updated.description == "Updated description"
    assert updated.agent_id == agent_id

    # Patch the secret
    patched = await patch_secret(
        conn=pool,
        secret_id=updated.id,
        developer_id=developer_id,
        input=PatchSecretInput(description="Patched description"),
    )

    # Verify the patch
    assert patched is not None
    assert patched.name == "UPDATE_TEST_KEY"
    assert patched.description == "Patched description"
    assert patched.agent_id == agent_id

    # Clean up
    await delete_secret(
        conn=pool,
        secret_id=result.id,
        developer_id=developer_id,
    )

    await pool.close()

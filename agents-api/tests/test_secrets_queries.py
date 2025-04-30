"""Tests for secrets queries."""

from uuid import uuid4

from agents_api.autogen.openapi_model import Secret
from agents_api.clients.pg import create_db_pool
from agents_api.queries.secrets.create import create_secret
from agents_api.queries.secrets.delete import delete_secret
from agents_api.queries.secrets.list import list_secrets
from agents_api.queries.secrets.update import update_secret
from ward import test

from tests.fixtures import pg_dsn, test_agent, test_developer_id


@test("query: create secret")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)

    # Create secret with both developer_id and agent_id
    agent_secret_data = {
        "name": "agent_api_key",
        "description": "An agent-specific API key",
        "value": "sk_agent_12345",
        "metadata": {"service": "agent_service", "environment": "test"},
    }

    agent_secret = await create_secret(
        developer_id=developer_id,
        agent_id=agent.id,
        name=agent_secret_data["name"],
        description=agent_secret_data["description"],
        value=agent_secret_data["value"],
        metadata=agent_secret_data["metadata"],
        connection_pool=pool,
    )

    assert agent_secret is not None
    assert isinstance(agent_secret, Secret)
    assert agent_secret.name == agent_secret_data["name"]
    assert agent_secret.developer_id == developer_id
    assert agent_secret.agent_id == agent.id
    assert agent_secret.value == "ENCRYPTED"


@test("query: list secrets")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)

    # Create test secrets first - use unique but valid identifiers
    secret_name1 = f"list_test_key_a{uuid4().hex[:6]}"
    secret_name2 = f"list_test_key_b{uuid4().hex[:6]}"

    await create_secret(
        developer_id=developer_id,
        agent_id=agent.id,
        name=secret_name1,
        description="Test secret 1 for listing",
        value="sk_test_list_1",
        connection_pool=pool,
    )

    await create_secret(
        developer_id=developer_id,
        agent_id=agent.id,
        name=secret_name2,
        description="Test secret 2 for listing",
        value="sk_test_list_2",
        connection_pool=pool,
    )

    # Test listing developer secrets
    secrets = await list_secrets(
        developer_id=developer_id,
        connection_pool=pool,
    )

    assert secrets is not None
    assert isinstance(secrets, list)
    assert len(secrets) > 0
    assert all(isinstance(secret, Secret) for secret in secrets)

    # Check if our test secrets are in the list
    created_secret_names = {secret.name for secret in secrets}
    assert secret_name1 in created_secret_names
    assert secret_name2 in created_secret_names

    # Test listing agent secrets
    agent_secrets = await list_secrets(
        developer_id=developer_id,
        agent_id=agent.id,
        connection_pool=pool,
    )

    assert agent_secrets is not None
    assert isinstance(agent_secrets, list)
    assert any(secret.name == secret_name2 for secret in agent_secrets)


@test("query: update secret")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)

    # Create a test secret first
    original_name = f"update_test_key_a{uuid4().hex[:6]}"
    original_secret = await create_secret(
        developer_id=developer_id,
        agent_id=agent.id,
        name=original_name,
        description="Original description",
        value="original_value",
        metadata={"original": True},
        connection_pool=pool,
    )

    # Update the secret
    updated_name = f"updated_key_b{uuid4().hex[:6]}"
    updated_description = "Updated description"
    updated_value = "updated_value"
    updated_metadata = {"updated": True, "timestamp": "now"}

    updated_secret = await update_secret(
        secret_id=original_secret.id,
        developer_id=developer_id,
        name=updated_name,
        description=updated_description,
        value=updated_value,
        metadata=updated_metadata,
        connection_pool=pool,
    )

    assert updated_secret is not None
    assert isinstance(updated_secret, Secret)
    assert updated_secret.id == original_secret.id
    assert updated_secret.name == updated_name
    assert updated_secret.description == updated_description
    assert updated_secret.value == "ENCRYPTED"
    assert updated_secret.metadata == updated_metadata

    # Test partial update (only update some fields)
    partial_description = "Partially updated description"
    partial_update = await update_secret(
        secret_id=original_secret.id,
        developer_id=developer_id,
        description=partial_description,
        connection_pool=pool,
    )

    assert partial_update is not None
    assert partial_update.name == updated_name  # Should remain from previous update
    assert partial_update.description == partial_description  # Should be updated
    assert partial_update.value == "ENCRYPTED"  # Should remain from previous update
    assert partial_update.metadata == updated_metadata  # Should remain from previous update


@test("query: delete secret")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)

    # Create a test secret first
    delete_test_name = f"delete_test_key_a{uuid4().hex[:6]}"
    test_secret = await create_secret(
        developer_id=developer_id,
        agent_id=agent.id,
        name=delete_test_name,
        description="Secret to be deleted",
        value="delete_me",
        connection_pool=pool,
    )

    # Delete the secret
    delete_result = await delete_secret(
        secret_id=test_secret.id,
        developer_id=developer_id,
        connection_pool=pool,
    )

    assert delete_result is not None
    assert delete_result.id == test_secret.id

    # Verify the secret is deleted by listing
    secrets = await list_secrets(
        developer_id=developer_id,
        connection_pool=pool,
    )

    # Make sure our deleted secret is not in the list
    assert not any(secret.id == test_secret.id for secret in secrets)

    # Create and delete an agent-specific secret
    agent_secret_name = f"agent_delete_test_b{uuid4().hex[:6]}"
    agent_secret = await create_secret(
        developer_id=developer_id,
        agent_id=agent.id,
        name=agent_secret_name,
        description="Agent secret to be deleted",
        value="agent_delete_me",
        connection_pool=pool,
    )

    # Delete with both developer_id and agent_id
    agent_delete_result = await delete_secret(
        secret_id=agent_secret.id,
        developer_id=developer_id,
        agent_id=agent.id,
        connection_pool=pool,
    )

    assert agent_delete_result is not None
    assert agent_delete_result.id == agent_secret.id

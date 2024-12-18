# Tests for agent queries
from uuid import UUID

import asyncpg
from uuid_extensions import uuid7
from ward import raises, test

from agents_api.autogen.openapi_model import (
    Agent,
    CreateAgentRequest,
    CreateOrUpdateAgentRequest,
    PatchAgentRequest,
    ResourceDeletedResponse,
    ResourceUpdatedResponse,
    UpdateAgentRequest,
)
from agents_api.clients.pg import create_db_pool
from agents_api.queries.agents import (
    create_agent,
    create_or_update_agent,
    delete_agent,
    get_agent,
    list_agents,
    patch_agent,
    update_agent,
)
from tests.fixtures import pg_dsn, test_agent, test_developer_id


@test("query: create agent sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that an agent can be successfully created."""

    pool = await create_db_pool(dsn=dsn)
    await create_agent(
        developer_id=developer_id,
        data=CreateAgentRequest(
            name="test agent",
            about="test agent about",
            model="gpt-4o-mini",
        ),
        connection_pool=pool,
    )


@test("query: create agent with instructions sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that an agent can be successfully created or updated."""

    pool = await create_db_pool(dsn=dsn)
    await create_or_update_agent(
        developer_id=developer_id,
        agent_id=uuid7(),
        data=CreateOrUpdateAgentRequest(
            name="test agent",
            canonical_name="test_agent2",
            about="test agent about",
            model="gpt-4o-mini",
            instructions=["test instruction"],
        ),
        connection_pool=pool,
    )


@test("query: update agent sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """Test that an existing agent's information can be successfully updated."""

    pool = await create_db_pool(dsn=dsn)
    result = await update_agent(
        agent_id=agent.id,
        developer_id=developer_id,
        data=UpdateAgentRequest(
            name="updated agent",
            about="updated agent about",
            model="gpt-4o-mini",
            default_settings={"temperature": 1.0},
            metadata={"hello": "world"},
        ),
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, ResourceUpdatedResponse)


@test("query: get agent not exists sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that retrieving a non-existent agent raises an exception."""

    agent_id = uuid7()
    pool = await create_db_pool(dsn=dsn)

    with raises(Exception):
        await get_agent(
            agent_id=agent_id, developer_id=developer_id, connection_pool=pool
        )


@test("query: get agent exists sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """Test that retrieving an existing agent returns the correct agent information."""

    pool = await create_db_pool(dsn=dsn)
    result = await get_agent(
        agent_id=agent.id,
        developer_id=developer_id,
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, Agent)


@test("query: list agents sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that listing agents returns a collection of agent information."""

    pool = await create_db_pool(dsn=dsn)
    result = await list_agents(developer_id=developer_id, connection_pool=pool)

    assert isinstance(result, list)
    assert all(isinstance(agent, Agent) for agent in result)


@test("query: patch agent sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """Test that an agent can be successfully patched."""

    pool = await create_db_pool(dsn=dsn)
    result = await patch_agent(
        agent_id=agent.id,
        developer_id=developer_id,
        data=PatchAgentRequest(
            name="patched agent",
            about="patched agent about",
            default_settings={"temperature": 1.0},
            metadata={"something": "else"},
        ),
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result, ResourceUpdatedResponse)


@test("query: delete agent sql")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """Test that an agent can be successfully deleted."""

    pool = await create_db_pool(dsn=dsn)
    delete_result = await delete_agent(
        agent_id=agent.id, developer_id=developer_id, connection_pool=pool
    )

    assert delete_result is not None
    assert isinstance(delete_result, ResourceDeletedResponse)

    with raises(Exception):
        await get_agent(
            developer_id=developer_id,
            agent_id=agent.id,
            connection_pool=pool,
        )

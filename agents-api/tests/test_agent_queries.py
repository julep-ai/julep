# Tests for agent queries
from uuid import uuid4

import asyncpg
from ward import raises, test

from agents_api.autogen.openapi_model import (
    Agent,
    CreateAgentRequest,
    CreateOrUpdateAgentRequest,
    PatchAgentRequest,
    ResourceUpdatedResponse,
    UpdateAgentRequest,
)
from agents_api.clients.pg import get_pg_client
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


@test("model: create agent")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    pool = await asyncpg.create_pool(dsn=dsn)
    async with get_pg_client(pool=pool) as client:
        await create_agent(
            developer_id=developer_id,
            data=CreateAgentRequest(
                name="test agent",
                about="test agent about",
                model="gpt-4o-mini",
            ),
            client=client,
        )


@test("model: create agent with instructions")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    pool = await asyncpg.create_pool(dsn=dsn)
    async with get_pg_client(pool=pool) as client:
        await create_agent(
            developer_id=developer_id,
            data=CreateAgentRequest(
                name="test agent",
                about="test agent about",
                model="gpt-4o-mini",
                instructions=["test instruction"],
            ),
            client=client,
        )


@test("model: create or update agent")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    pool = await asyncpg.create_pool(dsn=dsn)
    async with get_pg_client(pool=pool) as client:
        await create_or_update_agent(
            developer_id=developer_id,
            agent_id=uuid4(),
            data=CreateOrUpdateAgentRequest(
                name="test agent",
                about="test agent about",
                model="gpt-4o-mini",
                instructions=["test instruction"],
            ),
            client=client,
        )


@test("model: get agent not exists")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    agent_id = uuid4()
    pool = await asyncpg.create_pool(dsn=dsn)

    with raises(Exception):
        async with get_pg_client(pool=pool) as client:
            await get_agent(agent_id=agent_id, developer_id=developer_id, client=client)


@test("model: get agent exists")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    pool = await asyncpg.create_pool(dsn=dsn)
    async with get_pg_client(pool=pool) as client:
        result = await get_agent(agent_id=agent.id, developer_id=developer_id, client=client)

    assert result is not None
    assert isinstance(result, Agent)


@test("model: delete agent")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    pool = await asyncpg.create_pool(dsn=dsn)
    async with get_pg_client(pool=pool) as client:
        temp_agent = await create_agent(
            developer_id=developer_id,
            data=CreateAgentRequest(
                name="test agent",
                about="test agent about",
                model="gpt-4o-mini",
                instructions=["test instruction"],
            ),
            client=client,
        )

        # Delete the agent
        await delete_agent(agent_id=temp_agent.id, developer_id=developer_id, client=client)

        # Check that the agent is deleted
        with raises(Exception):
            await get_agent(agent_id=temp_agent.id, developer_id=developer_id, client=client)


@test("model: update agent")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    pool = await asyncpg.create_pool(dsn=dsn)
    async with get_pg_client(pool=pool) as client:
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
            client=client,
        )

    assert result is not None
    assert isinstance(result, ResourceUpdatedResponse)

    async with get_pg_client(pool=pool) as client:
        agent = await get_agent(
            agent_id=agent.id,
            developer_id=developer_id,
            client=client,
        )

    assert "test" not in agent.metadata


@test("model: patch agent")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    pool = await asyncpg.create_pool(dsn=dsn)
    async with get_pg_client(pool=pool) as client:
        result = await patch_agent(
            agent_id=agent.id,
            developer_id=developer_id,
            data=PatchAgentRequest(
                name="patched agent",
                about="patched agent about",
                default_settings={"temperature": 1.0},
                metadata={"something": "else"},
            ),
            client=client,
        )

    assert result is not None
    assert isinstance(result, ResourceUpdatedResponse)

    async with get_pg_client(pool=pool) as client:
        agent = await get_agent(
            agent_id=agent.id,
            developer_id=developer_id,
            client=client,
        )

    assert "hello" in agent.metadata


@test("model: list agents")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Tests listing all agents associated with a developer in the database. Verifies that the correct list of agents is retrieved."""

    pool = await asyncpg.create_pool(dsn=dsn)
    async with get_pg_client(pool=pool) as client:
        result = await list_agents(developer_id=developer_id, client=client)

    assert isinstance(result, list)
    assert all(isinstance(agent, Agent) for agent in result)

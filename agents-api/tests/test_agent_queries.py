# Tests for agent queries

from agents_api.autogen.openapi_model import (
    Agent,
    CreateAgentRequest,
    CreateOrUpdateAgentRequest,
    PatchAgentRequest,
    ResourceDeletedResponse,
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
from fastapi import HTTPException
from uuid_extensions import uuid7
import pytest

from tests.fixtures import pg_dsn, test_agent, test_developer_id, test_project


@pytest.mark.asyncio
async def test_query_create_agent_sql(dsn=pg_dsn, developer_id=test_developer_id):
    """query: create agent sql"""
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
    )  # type: ignore[not-callable]


@pytest.mark.asyncio
async def test_query_create_agent_with_project_sql(dsn=pg_dsn, developer_id=test_developer_id, project=test_project):
    """query: create agent with project sql"""
    """Test that an agent can be successfully created with a project."""

    pool = await create_db_pool(dsn=dsn)
    result = await create_agent(
        developer_id=developer_id,
        data=CreateAgentRequest(
            name="test agent with project",
            about="test agent about",
            model="gpt-4o-mini",
            project=project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert result.project == project.canonical_name


@pytest.mark.asyncio
async def test_query_create_agent_with_invalid_project_sql(dsn=pg_dsn, developer_id=test_developer_id):
    """query: create agent with invalid project sql"""
    """Test that creating an agent with an invalid project raises an exception."""

    pool = await create_db_pool(dsn=dsn)

    with pytest.pytest.raises(HTTPException) as exc:
        await create_agent(
            developer_id=developer_id,
            data=CreateAgentRequest(
                name="test agent with invalid project",
                about="test agent about",
                model="gpt-4o-mini",
                project="invalid_project",
            ),
            connection_pool=pool,
        )  # type: ignore[not-callable]

    assert exc.raised.status_code == 404
    assert "Project 'invalid_project' not found" in exc.raised.detail


@pytest.mark.asyncio
async def test_query_create_or_update_agent_sql(dsn=pg_dsn, developer_id=test_developer_id):
    """query: create or update agent sql"""
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
    )  # type: ignore[not-callable]


@pytest.mark.asyncio
async def test_query_create_or_update_agent_with_project_sql(dsn=pg_dsn, developer_id=test_developer_id, project=test_project):
    """query: create or update agent with project sql"""
    """Test that an agent can be successfully created or updated with a project."""

    pool = await create_db_pool(dsn=dsn)
    result = await create_or_update_agent(
        developer_id=developer_id,
        agent_id=uuid7(),
        data=CreateOrUpdateAgentRequest(
            name="test agent",
            canonical_name="test_agent_with_project",
            about="test agent about",
            model="gpt-4o-mini",
            instructions=["test instruction"],
            project=project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert result.project == project.canonical_name


@pytest.mark.asyncio
async def test_query_update_agent_sql(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """query: update agent sql"""
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
    )  # type: ignore[not-callable]

    assert result is not None
    assert isinstance(result, Agent)
    assert result.name == "updated agent"
    assert result.about == "updated agent about"
    assert result.model == "gpt-4o-mini"
    assert result.default_settings["temperature"] == 1.0
    assert result.metadata == {"hello": "world"}


@pytest.mark.asyncio
async def test_query_update_agent_with_project_sql(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, project=test_project):
    """query: update agent with project sql"""
    """Test that an existing agent's information can be successfully updated with a project."""

    pool = await create_db_pool(dsn=dsn)
    result = await update_agent(
        agent_id=agent.id,
        developer_id=developer_id,
        data=UpdateAgentRequest(
            name="updated agent with project",
            about="updated agent about",
            model="gpt-4o-mini",
            default_settings={"temperature": 1.0},
            metadata={"hello": "world"},
            project=project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert result is not None
    assert isinstance(result, Agent)
    assert result.project == project.canonical_name


@pytest.mark.asyncio
async def test_query_update_agent_project_does_not_exist(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """query: update agent, project does not exist"""
    """Test that an existing agent's information can be successfully updated with a project that does not exist."""

    pool = await create_db_pool(dsn=dsn)
    with pytest.pytest.raises(HTTPException) as exc:
        await update_agent(
            agent_id=agent.id,
            developer_id=developer_id,
            data=UpdateAgentRequest(
                name="updated agent with project",
                about="updated agent about",
                model="gpt-4o-mini",
                default_settings={"temperature": 1.0},
                metadata={"hello": "world"},
                project="invalid_project",
            ),
            connection_pool=pool,
        )  # type: ignore[not-callable]

    assert exc.raised.status_code == 404
    assert "Project 'invalid_project' not found" in exc.raised.detail


@pytest.mark.asyncio
async def test_query_patch_agent_sql(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """query: patch agent sql"""
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
    )  # type: ignore[not-callable]

    assert result is not None
    assert isinstance(result, Agent)
    assert result.name == "patched agent"
    assert result.about == "patched agent about"
    assert result.default_settings["temperature"] == 1.0


@pytest.mark.asyncio
async def test_query_patch_agent_with_project_sql(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, project=test_project):
    """query: patch agent with project sql"""
    """Test that an agent can be successfully patched with a project."""

    pool = await create_db_pool(dsn=dsn)
    result = await patch_agent(
        agent_id=agent.id,
        developer_id=developer_id,
        data=PatchAgentRequest(
            name="patched agent with project",
            about="patched agent about",
            default_settings={"temperature": 1.0},
            metadata={"something": "else"},
            project=project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]
    # Verify the agent is in the list of agents with the correct project
    agents = await list_agents(
        developer_id=developer_id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    # Find our patched agent in the list
    patched_agent = next((a for a in agents if a.id == agent.id), None)

    assert patched_agent is not None
    assert patched_agent.name == "patched agent with project"
    assert patched_agent.project == project.canonical_name

    assert result is not None
    assert isinstance(result, Agent)
    assert result.project == project.canonical_name


@pytest.mark.asyncio
async def test_query_patch_agent_project_does_not_exist(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """query: patch agent, project does not exist"""
    """Test that an agent can be successfully patched with a project that does not exist."""

    pool = await create_db_pool(dsn=dsn)
    with pytest.pytest.raises(HTTPException) as exc:
        await patch_agent(
            agent_id=agent.id,
            developer_id=developer_id,
            data=PatchAgentRequest(
                name="patched agent with project",
                about="patched agent about",
                default_settings={"temperature": 1.0},
                metadata={"something": "else"},
                project="invalid_project",
            ),
            connection_pool=pool,
        )  # type: ignore[not-callable]

    assert exc.raised.status_code == 404
    assert "Project 'invalid_project' not found" in exc.raised.detail


@pytest.mark.asyncio
async def test_query_get_agent_not_exists_sql(dsn=pg_dsn, developer_id=test_developer_id):
    """query: get agent not exists sql"""
    """Test that retrieving a non-existent agent raises an exception."""

    agent_id = uuid7()
    pool = await create_db_pool(dsn=dsn)

    with pytest.pytest.raises(Exception):
        await get_agent(agent_id=agent_id, developer_id=developer_id, connection_pool=pool)  # type: ignore[not-callable]


@pytest.mark.asyncio
async def test_query_get_agent_exists_sql(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    """query: get agent exists sql"""
    """Test that retrieving an existing agent returns the correct agent information."""

    pool = await create_db_pool(dsn=dsn)
    result = await get_agent(
        agent_id=agent.id,
        developer_id=developer_id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert result is not None
    assert isinstance(result, Agent)
    assert result.id == agent.id
    assert result.name == agent.name
    assert result.about == agent.about
    assert result.model == agent.model
    assert result.default_settings == agent.default_settings
    assert result.metadata == agent.metadata


@pytest.mark.asyncio
async def test_query_list_agents_sql(dsn=pg_dsn, developer_id=test_developer_id):
    """query: list agents sql"""
    """Test that listing agents returns a collection of agent information."""

    pool = await create_db_pool(dsn=dsn)
    result = await list_agents(developer_id=developer_id, connection_pool=pool)  # type: ignore[not-callable]

    assert isinstance(result, list)
    assert all(isinstance(agent, Agent) for agent in result)


@pytest.mark.asyncio
async def test_query_list_agents_with_project_filter_sql(dsn=pg_dsn, developer_id=test_developer_id, project=test_project):
    """query: list agents with project filter sql"""
    """Test that listing agents with a project filter returns the correct agents."""

    pool = await create_db_pool(dsn=dsn)

    # First create an agent with the specific project
    await create_agent(
        developer_id=developer_id,
        data=CreateAgentRequest(
            name="test agent for project filter",
            about="test agent about",
            model="gpt-4o-mini",
            project=project.canonical_name,
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]

    # Now fetch with project filter
    result = await list_agents(developer_id=developer_id, connection_pool=pool)  # type: ignore[not-callable]

    assert isinstance(result, list)
    assert all(isinstance(agent, Agent) for agent in result)
    assert any(agent.project == project.canonical_name for agent in result)


@pytest.mark.asyncio
async def test_query_list_agents_sql_invalid_sort_direction(dsn=pg_dsn, developer_id=test_developer_id):
    """query: list agents sql, invalid sort direction"""
    """Test that listing agents with an invalid sort direction raises an exception."""

    pool = await create_db_pool(dsn=dsn)
    with pytest.pytest.raises(HTTPException) as exc:
        await list_agents(
            developer_id=developer_id,
            connection_pool=pool,
            direction="invalid",
        )  # type: ignore[not-callable]

    assert exc.raised.status_code == 400
    assert exc.raised.detail == "Invalid sort direction"


@pytest.mark.asyncio
async def test_query_delete_agent_sql(dsn=pg_dsn, developer_id=test_developer_id):
    """query: delete agent sql"""
    """Test that an agent can be successfully deleted."""

    pool = await create_db_pool(dsn=dsn)
    create_result = await create_agent(
        developer_id=developer_id,
        data=CreateAgentRequest(
            name="test agent",
            about="test agent about",
            model="gpt-4o-mini",
        ),
        connection_pool=pool,
    )  # type: ignore[not-callable]
    delete_result = await delete_agent(
        agent_id=create_result.id,
        developer_id=developer_id,
        connection_pool=pool,
    )  # type: ignore[not-callable]

    assert delete_result is not None
    assert isinstance(delete_result, ResourceDeletedResponse)

    with pytest.pytest.raises(Exception):
        await get_agent(
            developer_id=developer_id,
            agent_id=create_result.id,
            connection_pool=pool,
        )  # type: ignore[not-callable]

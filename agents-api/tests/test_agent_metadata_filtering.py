"""
Tests for secure metadata filtering in agent queries
"""

from agents_api.autogen.openapi_model import CreateAgentRequest
from agents_api.clients.pg import create_db_pool
from agents_api.queries.agents.create_agent import create_agent
from agents_api.queries.agents.list_agents import list_agents
from ward import test

from .fixtures import pg_dsn, test_developer_id


@test("query: list_agents with metadata filtering")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that list_agents correctly filters by metadata."""
    pool = await create_db_pool(dsn=dsn)

    # Create test agents with different metadata
    agent1 = await create_agent(
        developer_id=developer_id,
        data=CreateAgentRequest(
            name="Test Agent 1",
            about="Test agent with specific metadata",
            model="gpt-4o-mini",
            metadata={"filter_key": "filter_value", "shared": "common"},
        ),
        connection_pool=pool,
    )

    agent2 = await create_agent(
        developer_id=developer_id,
        data=CreateAgentRequest(
            name="Test Agent 2",
            about="Test agent with different metadata",
            model="gpt-4o-mini",
            metadata={"other_key": "other_value", "shared": "common"},
        ),
        connection_pool=pool,
    )

    # List agents with specific metadata filter
    agents_filtered = await list_agents(
        developer_id=developer_id,
        metadata_filter={"filter_key": "filter_value"},
        connection_pool=pool,
    )

    # Verify correct filtering
    assert len(agents_filtered) >= 1
    assert any(a.id == agent1.id for a in agents_filtered)
    assert not any(a.id == agent2.id for a in agents_filtered)

    # List agents with shared metadata
    agents_shared = await list_agents(
        developer_id=developer_id,
        metadata_filter={"shared": "common"},
        connection_pool=pool,
    )

    # Verify both agents are returned
    assert len(agents_shared) >= 2
    assert any(a.id == agent1.id for a in agents_shared)
    assert any(a.id == agent2.id for a in agents_shared)


@test("query: list_agents with SQL injection attempt in metadata filter")
async def _(dsn=pg_dsn, developer_id=test_developer_id):
    """Test that list_agents safely handles metadata filters with SQL injection attempts."""
    pool = await create_db_pool(dsn=dsn)

    # Create a test agent with normal metadata
    agent_normal = await create_agent(
        developer_id=developer_id,
        data=CreateAgentRequest(
            name="Normal Agent",
            about="Agent with normal metadata",
            model="gpt-4o-mini",
            metadata={"test_key": "test_value"},
        ),
        connection_pool=pool,
    )

    # Create a test agent with special characters in metadata
    agent_special = await create_agent(
        developer_id=developer_id,
        data=CreateAgentRequest(
            name="Special Agent",
            about="Agent with special metadata",
            model="gpt-4o-mini",
            metadata={"special' SELECT * FROM agents--": "special_value"},
        ),
        connection_pool=pool,
    )

    # Attempt normal metadata filtering
    agents_normal = await list_agents(
        developer_id=developer_id,
        metadata_filter={"test_key": "test_value"},
        connection_pool=pool,
    )

    # Verify normal filtering works
    assert any(a.id == agent_normal.id for a in agents_normal)
    assert not any(a.id == agent_special.id for a in agents_normal)

    # Attempt filtering with SQL injection attempts
    injection_filters = [
        {"key' OR 1=1--": "value"},  # SQL injection in key
        {"key": "1' OR '1'='1"},  # SQL injection in value
        {"key' DROP TABLE agents--": "value"},  # Command injection in key
    ]

    for injection_filter in injection_filters:
        # These should safely execute without error
        agents_injection = await list_agents(
            developer_id=developer_id,
            metadata_filter=injection_filter,
            connection_pool=pool,
        )

        # Should not return all agents (which would happen if injection succeeded)
        assert len(agents_injection) == 0, (
            f"Should not match any agents with injection filter: {injection_filter}"
        )

    # Test for agent with special characters in metadata
    agents_special = await list_agents(
        developer_id=developer_id,
        metadata_filter={"special' SELECT * FROM agents--": "special_value"},
        connection_pool=pool,
    )

    # Verify exact matching works for special characters too (if using JSONB containment operator)
    assert len(agents_special) >= 1
    assert any(a.id == agent_special.id for a in agents_special)
    assert not any(a.id == agent_normal.id for a in agents_special)

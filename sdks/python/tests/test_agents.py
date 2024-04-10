from ward import test

from julep.api.types import (
    Agent,
)

from .fixtures import (
    client,
    async_client,
    mock_agent,
    mock_agent_update,
    test_agent,
)


@test("agents.create")
def _(agent=test_agent):
    assert isinstance(agent, Agent)
    assert hasattr(agent, "created_at")
    assert agent.name == mock_agent["name"]
    assert agent.about == mock_agent["about"]


@test("agents.get")
def _(client=client, agent=test_agent):
    response = client.agents.get(agent.id)
    assert isinstance(response, Agent)
    assert response.id == agent.id
    assert response.name == agent.name
    assert response.about == agent.about


@test("async agents.create, agents.get, agents.update & agents.delete")
async def _(client=async_client):
    agent = await client.agents.create(**mock_agent)

    assert isinstance(agent, Agent)
    assert hasattr(agent, "created_at")
    assert agent.name == mock_agent["name"]
    assert agent.about == mock_agent["about"]

    try:
        response = await client.agents.get(agent.id)
        assert isinstance(response, Agent)
        assert response.id == agent.id
        assert response.name == agent.name
        assert response.about == agent.about

        updated = await client.agents.update(agent_id=agent.id, **mock_agent_update)
        assert updated.name == mock_agent_update["name"]
        assert updated.about == mock_agent_update["about"]
        assert (
            updated.instructions[0]
            == mock_agent_update["instructions"][0]
        )
    finally:
        response = await client.agents.delete(agent.id)
        assert response is None


@test("agents.list")
def _(client=client):
    response = client.agents.list()
    assert len(response) > 0
    assert isinstance(response[0], Agent)


@test("async agents.list")
async def _(client=async_client):
    response = await client.agents.list()
    assert len(response) > 0
    assert isinstance(response[0], Agent)


@test("agents.update")
def _(client=client, agent=test_agent):
    response = client.agents.update(agent_id=agent.id, **mock_agent_update)

    assert isinstance(response, Agent)
    assert hasattr(response, "updated_at")
    assert response.name == mock_agent_update["name"]
    assert response.about == mock_agent_update["about"]
    assert (
        response.instructions[0]
        == mock_agent_update["instructions"][0]
    )


@test("agents.delete")
def _(client=client, agent=test_agent):
    response = client.agents.delete(agent.id)

    assert response is None

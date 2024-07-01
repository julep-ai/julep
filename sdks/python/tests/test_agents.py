from ward import test

from julep import AsyncClient
from julep.api.types import (
    Agent,
)

from .fixtures import (
    client,
    mock_agent_update,
    mock_agent,
    test_agent,
    test_agent_async,
    TEST_API_KEY,
    TEST_API_URL,
)


@test("agents: agents.create")
def _(agent=test_agent):
    assert isinstance(agent, Agent)
    assert hasattr(agent, "created_at")
    assert agent.name == mock_agent["name"]
    assert agent.about == mock_agent["about"]


@test("agents: agents.create multiple instructions")
def _(client=client):
    attrs = {**mock_agent, "instructions": ["instruction1", "instruction2"]}
    response = client.agents.create(**attrs)

    assert isinstance(response, Agent)


@test("agents: agents.get")
def _(client=client, agent=test_agent):
    response = client.agents.get(agent.id)
    assert isinstance(response, Agent)
    assert response.id == agent.id
    assert response.name == agent.name
    assert response.about == agent.about


@test("agents: async agents.create, agents.get, agents.update & agents.delete")
async def _(agent=test_agent_async):
    client = AsyncClient(
        api_key=TEST_API_KEY,
        base_url=TEST_API_URL,
    )

    assert isinstance(agent, Agent)
    assert agent.name == mock_agent["name"]
    assert agent.about == mock_agent["about"]

    response = await client.agents.get(agent.id)
    assert isinstance(response, Agent)
    assert response.id == agent.id
    assert response.name == agent.name
    assert response.about == agent.about

    updated = await client.agents.update(agent_id=agent.id, **mock_agent_update)
    assert updated.name == mock_agent_update["name"]
    assert updated.about == mock_agent_update["about"]


@test("agents: agents.list")
def _(client=client, _=test_agent):
    response = client.agents.list()
    assert len(response) > 0
    assert isinstance(response[0], Agent)


# @test("agents: async agents.list")
# async def _(client=async_client, _=test_agent_async):
#     response = await client.agents.list()
#     assert len(response) > 0
#     assert isinstance(response[0], Agent)


@test("agents: agents.update")
def _(client=client, agent=test_agent):
    response = client.agents.update(agent_id=agent.id, name=mock_agent_update["name"])

    assert isinstance(response, Agent)
    assert response.name == mock_agent_update["name"]


@test("agents: agents.update with overwrite")
def _(client=client, agent=test_agent):
    response = client.agents.update(
        agent_id=agent.id, overwrite=True, name="overwrite", about="about overwritten"
    )

    assert isinstance(response, Agent)
    assert hasattr(response, "updated_at")
    assert response.name


# @test("agents: agents.delete")
# def _(client=client, agent=test_agent):
#     response = client.agents.delete(agent.id)

#     assert response is None

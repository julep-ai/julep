from ward import test


from julep import AsyncClient
from julep.api.types import ResourceCreatedResponse, ResourceUpdatedResponse, Tool

from .fixtures import (
    test_tool,
    test_agent,
    client,
    async_client,
    TEST_API_KEY,
    TEST_API_URL,
)


@test("tools: tools.create")
def _(client=client, tool=test_tool):
    created_tool, _ = tool

    assert isinstance(created_tool, ResourceCreatedResponse)
    assert hasattr(created_tool, "created_at")


@test("tools: tools.update")
def _(client=client, tool=test_tool):
    created_tool, agent = tool
    response = client.tools.update(
        agent_id=agent.id,
        tool_id=created_tool.id,
        function={
            "description": "test description",
            "name": "test name",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_arg": {"type": "string", "default": "test val"},
                },
            },
        },
    )

    assert isinstance(response, ResourceUpdatedResponse)


@test("tools: tools.list")
def _(client=client, tool=test_tool):
    created_tool, agent = tool

    response = client.tools.get(agent_id=agent.id)

    assert len(response) > 0
    assert isinstance(response[0], Tool)


@test("tools: async tools.create, tools.get, tools.update & tools.delete")
async def _(client=async_client, tool=test_tool):
    tool, agent = tool

    response = await client.tools.get(agent_id=agent.id)
    assert len(response) > 0
    assert isinstance(response[0], Tool)

    response = await client.tools.update(
        agent_id=agent.id,
        tool_id=tool.id,
        function={
            "description": "test description",
            "name": "test name",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_arg": {"type": "string", "default": "test val"},
                },
            },
        },
    )
    assert isinstance(response, ResourceUpdatedResponse)
    assert response.updated_at


@test("tools: async tools.get")
async def _(client=async_client, tool=test_tool):
    _, agent = tool
    response = await client.tools.get(agent_id=agent.id)
    assert len(response) > 0
    assert isinstance(response[0], Tool)


@test("tools: async tools.get empty")
async def _(client=async_client, agent=test_agent):
    response = await client.tools.get(agent_id=agent.id)
    assert len(response) == 0


@test("tools: async tools.update")
async def _(tool=test_tool):
    client = AsyncClient(
        api_key=TEST_API_KEY,
        base_url=TEST_API_URL,
    )

    tool, agent = tool
    response = await client.tools.update(
        agent_id=agent.id,
        tool_id=tool.id,
        function={
            "description": "test description",
            "name": "test name",
            "parameters": {
                "type": "object",
                "properties": {
                    "test_arg": {"type": "string", "default": "test val"},
                },
            },
        },
    )

    assert response.updated_at

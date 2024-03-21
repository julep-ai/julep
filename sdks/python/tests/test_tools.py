from ward import test

from julep.api.types import ResourceCreatedResponse, ResourceUpdatedResponse, Tool

from .fixtures import (
    test_tool,
    test_agent,
    client,
    setup_tool_async,
    setup_agent_async,
    async_client,
)


@test("tools.create")
def _(client=client, tool=test_tool):
    agent, created_tool = tool

    try:
        assert isinstance(created_tool, ResourceCreatedResponse)
        assert hasattr(created_tool, "created_at")
    finally:
        client.tools.delete(
            agent_id=agent.id,
            tool_id=created_tool.id,
        )
        client.agents.delete(agent_id=agent.id)


@test("tools.update")
def _(client=client, tool=test_tool):
    agent, created_tool = tool
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

    try:
        assert isinstance(response, ResourceUpdatedResponse)
        assert response.updated_at
    finally:
        client.tools.delete(
            agent_id=agent.id,
            tool_id=created_tool.id,
        )
        client.agents.delete(agent_id=agent.id)


@test("tools.list")
def _(client=client, tool=test_tool):
    agent, created_tool = tool

    response = client.tools.get(agent_id=agent.id)

    try:
        assert len(response) > 0
        assert isinstance(response[0], Tool)
    finally:
        client.tools.delete(
            agent_id=agent.id,
            tool_id=created_tool.id,
        )
        client.agents.delete(agent_id=agent.id)


@test("tools.delete")
def _(client=client, agent=test_agent, tool=test_tool):
    agent, created_tool = tool
    response = client.tools.delete(
        agent_id=agent.id,
        tool_id=created_tool.id,
    )
    assert response is None


@test("async tools.create, tools.get, tools.update & tools.delete")
async def _(client=async_client):
    agent = await setup_agent_async(client)
    tool = await setup_tool_async(client, agent)

    try:
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

    finally:
        response = await client.tools.delete(
            agent_id=agent.id,
            tool_id=tool.id,
        )
        assert response is None
        response = await client.agents.delete(agent_id=agent.id)
        assert response is None


# @test("async tools.get")
# async def _(client=async_client):
#     response = await client.tools.get(agent_id=uuid4())
#     assert len(response) > 0
#     assert isinstance(response[0], Tool)


# @test("tools.create")
# async def _(client=async_client):
#     response = await client.tools.create(
#         agent_id=uuid4(),
#         tool={
#             "type": "function",
#             "function": {
#                 "description": "test description",
#                 "name": "test name",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "test_arg": {"type": "string", "default": "test val"},
#                     },
#                 },
#             },
#         },
#     )

#     assert isinstance(response, ResourceCreatedResponse)
#     assert response.created_at


# @test("async tools.update")
# async def _(client=async_client):
#     response = await client.tools.update(
#         agent_id=uuid4(),
#         tool_id=uuid4(),
#         function={
#             "description": "test description",
#             "name": "test name",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "test_arg": {"type": "string", "default": "test val"},
#                 },
#             },
#         },
#     )

#     assert isinstance(response, ResourceUpdatedResponse)
#     assert response.updated_at


# @test("async tools.delete")
# async def _(client=async_client):
#     response = await client.tools.delete(
#         agent_id=uuid4(),
#         tool_id=uuid4(),
#     )
#     assert response is None

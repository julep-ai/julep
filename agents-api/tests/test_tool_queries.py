# # Tests for tool queries

# from ward import test

# from agents_api.autogen.openapi_model import (
#     CreateToolRequest,
#     PatchToolRequest,
#     Tool,
#     UpdateToolRequest,
# )
# from agents_api.queries.tools.create_tools import create_tools
# from agents_api.queries.tools.delete_tool import delete_tool
# from agents_api.queries.tools.get_tool import get_tool
# from agents_api.queries.tools.list_tools import list_tools
# from agents_api.queries.tools.patch_tool import patch_tool
# from agents_api.queries.tools.update_tool import update_tool
# from tests.fixtures import cozo_client, test_agent, test_developer_id, test_tool


# @test("query: create tool")
# def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
#     function = {
#         "name": "hello_world",
#         "description": "A function that prints hello world",
#         "parameters": {"type": "object", "properties": {}},
#     }

#     tool = {
#         "function": function,
#         "name": "hello_world",
#         "type": "function",
#     }

#     result = create_tools(
#         developer_id=developer_id,
#         agent_id=agent.id,
#         data=[CreateToolRequest(**tool)],
#         client=client,
#     )

#     assert result is not None
#     assert isinstance(result[0], Tool)


# @test("query: delete tool")
# def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
#     function = {
#         "name": "temp_temp",
#         "description": "A function that prints hello world",
#         "parameters": {"type": "object", "properties": {}},
#     }

#     tool = {
#         "function": function,
#         "name": "temp_temp",
#         "type": "function",
#     }

#     [tool, *_] = create_tools(
#         developer_id=developer_id,
#         agent_id=agent.id,
#         data=[CreateToolRequest(**tool)],
#         client=client,
#     )

#     result = delete_tool(
#         developer_id=developer_id,
#         agent_id=agent.id,
#         tool_id=tool.id,
#         client=client,
#     )

#     assert result is not None


# @test("query: get tool")
# def _(
#     client=cozo_client, developer_id=test_developer_id, tool=test_tool, agent=test_agent
# ):
#     result = get_tool(
#         developer_id=developer_id,
#         agent_id=agent.id,
#         tool_id=tool.id,
#         client=client,
#     )

#     assert result is not None


# @test("query: list tools")
# def _(
#     client=cozo_client, developer_id=test_developer_id, agent=test_agent, tool=test_tool
# ):
#     result = list_tools(
#         developer_id=developer_id,
#         agent_id=agent.id,
#         client=client,
#     )

#     assert result is not None
#     assert all(isinstance(tool, Tool) for tool in result)


# @test("query: patch tool")
# def _(
#     client=cozo_client, developer_id=test_developer_id, agent=test_agent, tool=test_tool
# ):
#     patch_data = PatchToolRequest(
#         **{
#             "name": "patched_tool",
#             "function": {
#                 "description": "A patched function that prints hello world",
#             },
#         }
#     )

#     result = patch_tool(
#         developer_id=developer_id,
#         agent_id=agent.id,
#         tool_id=tool.id,
#         data=patch_data,
#         client=client,
#     )

#     assert result is not None

#     tool = get_tool(
#         developer_id=developer_id,
#         agent_id=agent.id,
#         tool_id=tool.id,
#         client=client,
#     )

#     assert tool.name == "patched_tool"
#     assert tool.function.description == "A patched function that prints hello world"
#     assert tool.function.parameters


# @test("query: update tool")
# def _(
#     client=cozo_client, developer_id=test_developer_id, agent=test_agent, tool=test_tool
# ):
#     update_data = UpdateToolRequest(
#         name="updated_tool",
#         description="An updated description",
#         type="function",
#         function={
#             "description": "An updated function that prints hello world",
#         },
#     )

#     result = update_tool(
#         developer_id=developer_id,
#         agent_id=agent.id,
#         tool_id=tool.id,
#         data=update_data,
#         client=client,
#     )

#     assert result is not None

#     tool = get_tool(
#         developer_id=developer_id,
#         agent_id=agent.id,
#         tool_id=tool.id,
#         client=client,
#     )

#     assert tool.name == "updated_tool"
#     assert not tool.function.parameters

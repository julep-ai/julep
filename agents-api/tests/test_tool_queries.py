# # Tests for tool queries

from ward import test

from agents_api.autogen.openapi_model import (
    CreateToolRequest,
    PatchToolRequest,
    Tool,
    UpdateToolRequest,
)
from agents_api.queries.tools.create_tools import create_tools
from agents_api.queries.tools.delete_tool import delete_tool
from agents_api.queries.tools.get_tool import get_tool
from agents_api.queries.tools.list_tools import list_tools
from agents_api.queries.tools.patch_tool import patch_tool
from agents_api.queries.tools.update_tool import update_tool
from tests.fixtures import test_agent, test_developer_id, pg_dsn, test_tool
from agents_api.clients.pg import create_db_pool


@test("query: create tool")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)
    function = {
        "name": "hello_world",
        "description": "A function that prints hello world",
        "parameters": {"type": "object", "properties": {}},
    }

    tool = {
        "function": function,
        "name": "hello_world",
        "type": "function",
    }

    result = await create_tools(
        developer_id=developer_id,
        agent_id=agent.id,
        data=[CreateToolRequest(**tool)],
        connection_pool=pool,
    )

    assert result is not None
    assert isinstance(result[0], Tool)


@test("query: delete tool")
async def _(dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent):
    pool = await create_db_pool(dsn=dsn)
    function = {
        "name": "temp_temp",
        "description": "A function that prints hello world",
        "parameters": {"type": "object", "properties": {}},
    }

    tool = {
        "function": function,
        "name": "temp_temp",
        "type": "function",
    }

    [tool, *_] = await create_tools(
        developer_id=developer_id,
        agent_id=agent.id,
        data=[CreateToolRequest(**tool)],
        connection_pool=pool,
    )

    result = delete_tool(
        developer_id=developer_id,
        agent_id=agent.id,
        tool_id=tool.id,
        connection_pool=pool,
    )

    assert result is not None


@test("query: get tool")
async def _(
    dsn=pg_dsn, developer_id=test_developer_id, tool=test_tool, agent=test_agent
):
    pool = await create_db_pool(dsn=dsn)
    result = get_tool(
        developer_id=developer_id,
        agent_id=agent.id,
        tool_id=tool.id,
        connection_pool=pool,
    )

    assert result is not None


@test("query: list tools")
async def _(
    dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, tool=test_tool
):
    pool = await create_db_pool(dsn=dsn)
    result = await list_tools(
        developer_id=developer_id,
        agent_id=agent.id,
        connection_pool=pool,
    )

    assert result is not None
    assert all(isinstance(tool, Tool) for tool in result)


@test("query: patch tool")
async def _(
    dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, tool=test_tool
):
    pool = await create_db_pool(dsn=dsn)
    patch_data = PatchToolRequest(
        **{
            "name": "patched_tool",
            "function": {
                "description": "A patched function that prints hello world",
                "parameters": {"param1": "value1"},
            },
        }
    )

    result = await patch_tool(
        developer_id=developer_id,
        agent_id=agent.id,
        tool_id=tool.id,
        data=patch_data,
        connection_pool=pool,
    )

    assert result is not None

    tool = await get_tool(
        developer_id=developer_id,
        agent_id=agent.id,
        tool_id=tool.id,
        connection_pool=pool,
    )

    assert tool.name == "patched_tool"
    assert tool.function.description == "A patched function that prints hello world"
    assert tool.function.parameters


@test("query: update tool")
async def _(
    dsn=pg_dsn, developer_id=test_developer_id, agent=test_agent, tool=test_tool
):
    pool = await create_db_pool(dsn=dsn)
    update_data = UpdateToolRequest(
        name="updated_tool",
        description="An updated description",
        type="function",
        function={
            "description": "An updated function that prints hello world",
        },
    )

    result = await update_tool(
        developer_id=developer_id,
        agent_id=agent.id,
        tool_id=tool.id,
        data=update_data,
        connection_pool=pool,
    )

    assert result is not None

    tool = await get_tool(
        developer_id=developer_id,
        agent_id=agent.id,
        tool_id=tool.id,
        connection_pool=pool,
    )

    assert tool.name == "updated_tool"
    assert not tool.function.parameters

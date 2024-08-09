# Tests for tool queries
from uuid import uuid4

from cozo_migrate.api import apply, init
from pycozo import Client
from ward import test

from agents_api.autogen.Tools import (
    CreateToolsRequest,
    DeleteToolRequest,
    GetToolRequest,
    ListToolsRequest,
)
from agents_api.models.tools.create_tools import create_tools
from agents_api.models.tools.delete_tool import delete_tool
from agents_api.models.tools.get_tool import get_tool
from agents_api.models.tools.list_tools import list_tools


def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("model: create tool")
def _():
    client = cozo_client()
    developer_id = uuid4()
    agent_id = uuid4()

    tool = {
        "name": "hello_world",
        "description": "A function that prints hello world",
        "parameters": {"type": "object", "properties": {}},
    }

    result = create_tools(
        developer_id=developer_id,
        agent_id=agent_id,
        data=CreateToolsRequest(tools=[tool]),
        client=client,
    )

    assert result is not None
    assert isinstance(result[0], dict)


@test("model: delete tool")
def _():
    client = cozo_client()
    developer_id = uuid4()
    agent_id = uuid4()
    tool_id = uuid4()

    tool = {
        "name": "hello_world",
        "description": "A function that prints hello world",
        "parameters": {"type": "object", "properties": {}},
    }

    create_tools(
        developer_id=developer_id,
        agent_id=agent_id,
        data=CreateToolsRequest(tools=[tool]),
        client=client,
    )

    result = delete_tool(
        developer_id=developer_id,
        agent_id=agent_id,
        tool_id=tool_id,
        data=DeleteToolRequest(),
        client=client,
    )

    assert result is not None
    assert result["id"] == str(tool_id)


@test("model: get tool")
def _():
    client = cozo_client()
    developer_id = uuid4()
    agent_id = uuid4()
    tool_id = uuid4()

    tool = {
        "name": "hello_world",
        "description": "A function that prints hello world",
        "parameters": {"type": "object", "properties": {}},
    }

    create_tools(
        developer_id=developer_id,
        agent_id=agent_id,
        data=CreateToolsRequest(tools=[tool]),
        client=client,
    )

    result = get_tool(
        developer_id=developer_id,
        agent_id=agent_id,
        tool_id=tool_id,
        data=GetToolRequest(),
        client=client,
    )

    assert result is not None
    assert isinstance(result, dict)


@test("model: list tools")
def _():
    client = cozo_client()
    developer_id = uuid4()
    agent_id = uuid4()

    tool = {
        "name": "hello_world",
        "description": "A function that prints hello world",
        "parameters": {"type": "object", "properties": {}},
    }

    create_tools(
        developer_id=developer_id,
        agent_id=agent_id,
        data=CreateToolsRequest(tools=[tool]),
        client=client,
    )

    result = list_tools(
        developer_id=developer_id,
        agent_id=agent_id,
        data=ListToolsRequest(),
        client=client,
    )

    assert result is not None
    assert all(isinstance(tool, dict) for tool in result)

from uuid import uuid4

from ward import test

from julep_ai.api.types import (
    Agent,
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
    AdditionalInfo,
    Tool,
)

from .fixtures import async_client, client


@test("agents.get")
def _(client=client):
    response = client.agents.get(uuid4())
    assert isinstance(response, Agent)


@test("async agents.get")
async def _(client=async_client):
    response = await client.agents.get(uuid4())
    assert isinstance(response, Agent)


@test("agents.create")
def _(client=client):
    response = client.agents.create(
        name="test agent",
        about="test agent about",
        instructions=["test agent instructions"],
        default_settings={"temperature": 0.5},
    )

    assert isinstance(response, ResourceCreatedResponse)
    assert response.created_at


@test("async agents.create")
async def _(client=async_client):
    response = await client.agents.create(
        name="test agent",
        about="test agent about",
        instructions=["test agent instructions"],
        default_settings={"temperature": 0.5},
    )

    assert isinstance(response, ResourceCreatedResponse)
    assert response.created_at


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
def _(client=client):
    response = client.agents.update(
        uuid4(),
        name="test user",
        about="test user about",
        instructions=["test agent instructions"],
        default_settings={"temperature": 0.5},
        model="some model",
    )

    assert isinstance(response, ResourceUpdatedResponse)
    assert response.updated_at


@test("agents.get_additional_info")
def _(client=client):
    response = client.agents.get_additional_info(uuid4())
    assert len(response) > 0
    assert isinstance(response[0], AdditionalInfo)


@test("agents.create_additional_info")
def _(client=client):
    response = client.agents.create_additional_info(
        uuid4(), doc={"title": "test title", "content": "test content"}
    )
    assert isinstance(response, ResourceCreatedResponse)


@test("agents.delete_additional_info")
def _(client=client):
    response = client.agents.delete_additional_info(
        uuid4(),
        additional_info_id=uuid4(),
    )
    assert response is None


@test("agents.get_tools")
def _(client=client):
    response = client.agents.get_tools(uuid4())
    assert len(response) > 0
    assert isinstance(response[0], Tool)


@test("agents.create_tool")
def _(client=client):
    response = client.agents.create_tool(
        uuid4(),
        tool={
            "type": "function",
            "definition": {
                "description": "test description",
                "name": "test name",
                "parameters": {"test_arg": "test val"},
            },
        },
    )

    assert isinstance(response, ResourceCreatedResponse)
    assert response.created_at


@test("agents.update_tool")
def _(client=client):
    response = client.agents.update_tool(
        uuid4(),
        uuid4(),
        definition={
            "description": "test description",
            "name": "test name",
            "parameters": {"test_arg": "test val"},
        },
    )

    assert isinstance(response, ResourceUpdatedResponse)
    assert response.updated_at


@test("agents.delete_tool")
def _(client=client):
    response = client.agents.delete_tool(
        uuid4(),
        uuid4(),
    )
    assert response is None


@test("async agents.update")
async def _(client=async_client):
    response = await client.agents.update(
        uuid4(),
        name="test user",
        about="test user about",
        instructions=["test agent instructions"],
        default_settings={"temperature": 0.5},
        model="some model",
    )

    assert isinstance(response, ResourceUpdatedResponse)
    assert response.updated_at


@test("async agents.get_additional_info")
async def _(client=async_client):
    response = await client.agents.get_additional_info(uuid4())
    assert len(response) > 0
    assert isinstance(response[0], AdditionalInfo)


@test("async agents.create_additional_info")
async def _(client=async_client):
    response = await client.agents.create_additional_info(
        uuid4(), doc={"title": "test title", "content": "test content"}
    )
    assert isinstance(response, ResourceCreatedResponse)


@test("async agents.delete_additional_info")
async def _(client=async_client):
    response = await client.agents.delete_additional_info(
        uuid4(),
        additional_info_id=uuid4(),
    )
    assert response is None


@test("async agents.get_tools")
async def _(client=async_client):
    response = await client.agents.get_tools(uuid4())
    assert len(response) > 0
    assert isinstance(response[0], Tool)


@test("agents.delete")
def _(client=client):
    response = client.agents.delete(
        uuid4(),
    )

    assert response is None


@test("async agents.delete")
async def _(client=async_client):
    response = await client.agents.delete(
        uuid4(),
    )

    assert response is None


@test("agents.create_tool")
async def _(client=async_client):
    response = await client.agents.create_tool(
        uuid4(),
        tool={
            "type": "function",
            "definition": {
                "description": "test description",
                "name": "test name",
                "parameters": {"test_arg": "test val"},
            },
        },
    )

    assert isinstance(response, ResourceCreatedResponse)
    assert response.created_at


@test("async agents.update_tool")
async def _(client=async_client):
    response = await client.agents.update_tool(
        uuid4(),
        uuid4(),
        definition={
            "description": "test description",
            "name": "test name",
            "parameters": {"test_arg": "test val"},
        },
    )

    assert isinstance(response, ResourceUpdatedResponse)
    assert response.updated_at


@test("async agents.delete_tool")
async def _(client=async_client):
    response = await client.agents.delete_tool(
        uuid4(),
        uuid4(),
    )
    assert response is None

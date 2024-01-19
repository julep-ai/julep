from uuid import uuid4

from ward import test

from julep_ai.api.types import (
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
    Tool,
)

from .fixtures import async_client, client


@test("tools.get")
def _(client=client):
    response = client.tools.get(agent_id=uuid4())
    assert len(response) > 0
    assert isinstance(response[0], Tool)


@test("tools.create")
def _(client=client):
    response = client.tools.create(
        agent_id=uuid4(),
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


@test("tools.update")
def _(client=client):
    response = client.tools.update(
        agent_id=uuid4(),
        tool_id=uuid4(),
        definition={
            "description": "test description",
            "name": "test name",
            "parameters": {"test_arg": "test val"},
        },
    )

    assert isinstance(response, ResourceUpdatedResponse)
    assert response.updated_at


@test("tools.delete")
def _(client=client):
    response = client.tools.delete(
        agent_id=uuid4(),
        tool_id=uuid4(),
    )
    assert response is None


@test("async tools.get")
async def _(client=async_client):
    response = await client.tools.get(agent_id=uuid4())
    assert len(response) > 0
    assert isinstance(response[0], Tool)


@test("tools.create")
async def _(client=async_client):
    response = await client.tools.create(
        agent_id=uuid4(),
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


@test("async tools.update")
async def _(client=async_client):
    response = await client.tools.update(
        agent_id=uuid4(),
        tool_id=uuid4(),
        definition={
            "description": "test description",
            "name": "test name",
            "parameters": {"test_arg": "test val"},
        },
    )

    assert isinstance(response, ResourceUpdatedResponse)
    assert response.updated_at


@test("async tools.delete")
async def _(client=async_client):
    response = await client.tools.delete(
        agent_id=uuid4(),
        tool_id=uuid4(),
    )
    assert response is None

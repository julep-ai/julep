from uuid import uuid4

from ward import test

from julep.api.types import (
    Agent,
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

    assert isinstance(response, Agent)
    assert response.created_at


@test("async agents.create")
async def _(client=async_client):
    response = await client.agents.create(
        name="test agent",
        about="test agent about",
        instructions=["test agent instructions"],
        default_settings={"temperature": 0.5},
    )

    assert isinstance(response, Agent)
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
        agent_id=uuid4(),
        name="test user",
        about="test user about",
        instructions=["test agent instructions"],
        default_settings={"temperature": 0.5},
        model="some model",
    )

    assert isinstance(response, Agent)
    assert response.updated_at


@test("async agents.update")
async def _(client=async_client):
    response = await client.agents.update(
        agent_id=uuid4(),
        name="test user",
        about="test user about",
        instructions=["test agent instructions"],
        default_settings={"temperature": 0.5},
        model="some model",
    )

    assert isinstance(response, Agent)
    assert response.updated_at


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

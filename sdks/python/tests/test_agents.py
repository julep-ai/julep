from uuid import uuid4

from ward import test

from julep_ai.api.types import Agent, ResourceCreatedResponse

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

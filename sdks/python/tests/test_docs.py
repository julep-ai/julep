from uuid import uuid4

from ward import test

from julep.api.types import (
    Doc,
)

from .fixtures import async_client, client


@test("agent docs.get")
def _(client=client):
    response = client.docs.get(agent_id=uuid4())
    assert len(response) > 0
    assert isinstance(response[0], Doc)


@test("user docs.get")
def _(client=client):
    response = client.docs.get(user_id=uuid4())
    assert len(response) > 0
    assert isinstance(response[0], Doc)


@test("agent docs.create")
def _(client=client):
    response = client.docs.create(
        agent_id=uuid4(), doc={"title": "test title", "content": "test content"}
    )
    assert isinstance(response, Doc)


@test("user docs.create")
def _(client=client):
    response = client.docs.create(
        user_id=uuid4(), doc={"title": "test title", "content": "test content"}
    )
    assert isinstance(response, Doc)


@test("agent docs.delete")
def _(client=client):
    response = client.docs.delete(
        agent_id=uuid4(),
        doc_id=uuid4(),
    )
    assert response is None


@test("user docs.delete")
def _(client=client):
    response = client.docs.delete(
        user_id=uuid4(),
        doc_id=uuid4(),
    )
    assert response is None


@test("async agent docs.get")
async def _(client=async_client):
    response = await client.docs.get(agent_id=uuid4())
    assert len(response) > 0
    assert isinstance(response[0], Doc)


@test("async user docs.get")
async def _(client=async_client):
    response = await client.docs.get(user_id=uuid4())
    assert len(response) > 0
    assert isinstance(response[0], Doc)


@test("async agent docs.create")
async def _(client=async_client):
    response = await client.docs.create(
        agent_id=uuid4(), doc={"title": "test title", "content": "test content"}
    )
    assert isinstance(response, Doc)


@test("async user docs.create")
async def _(client=async_client):
    response = await client.docs.create(
        user_id=uuid4(), doc={"title": "test title", "content": "test content"}
    )
    assert isinstance(response, Doc)


@test("async agent docs.delete")
async def _(client=async_client):
    response = await client.docs.delete(
        agent_id=uuid4(),
        doc_id=uuid4(),
    )
    assert response is None


@test("async user docs.delete")
async def _(client=async_client):
    response = await client.docs.delete(
        user_id=uuid4(),
        doc_id=uuid4(),
    )
    assert response is None

from uuid import uuid4

from ward import test

from julep.api.types import User, ResourceCreatedResponse, ResourceUpdatedResponse

from .fixtures import async_client, client


@test("users.get")
def _(client=client):
    response = client.users.get(uuid4())
    assert isinstance(response, User)


@test("async users.get")
async def _(client=async_client):
    response = await client.users.get(uuid4())
    assert isinstance(response, User)


@test("users.create")
def _(client=client):
    response = client.users.create(
        name="test user",
        about="test user about",
    )

    assert isinstance(response, User)
    assert response.created_at


@test("async users.create")
async def _(client=async_client):
    response = await client.users.create(
        name="test user",
        about="test user about",
    )

    assert isinstance(response, User)
    assert response.created_at


@test("users.list")
def _(client=client):
    response = client.users.list()
    assert len(response) > 0
    assert isinstance(response[0], User)


@test("async users.list")
async def _(client=async_client):
    response = await client.users.list()
    assert len(response) > 0
    assert isinstance(response[0], User)


@test("users.update")
def _(client=client):
    response = client.users.update(
        user_id=uuid4(),
        name="test user",
        about="test user about",
    )

    assert isinstance(response, User)
    assert response.updated_at


@test("async users.update")
async def _(client=async_client):
    response = await client.users.update(
        user_id=uuid4(),
        name="test user",
        about="test user about",
    )

    assert isinstance(response, User)
    assert response.updated_at


@test("users.delete")
def _(client=client):
    response = client.users.delete(
        user_id=uuid4(),
    )

    assert response is None


@test("async users.delete")
async def _(client=async_client):
    response = await client.users.delete(
        user_id=uuid4(),
    )

    assert response is None

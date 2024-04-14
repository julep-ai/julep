from ward import test

from julep.api.types import User

from .fixtures import (
    async_client,
    client,
    mock_user,
    mock_user_update,
    test_user,
    test_user_async,
)


@test("users: users.create")
def _(user=test_user):
    assert isinstance(user, User)
    assert hasattr(user, "created_at")
    assert user.name == mock_user["name"]
    assert user.about == mock_user["about"]


@test("users: async users.create, users.get, users.update & users.delete")
async def _(client=async_client, user=test_user_async):
    assert isinstance(user, User)
    assert hasattr(user, "created_at")
    assert user.name == mock_user["name"]
    assert user.about == mock_user["about"]

    response = await client.users.get(user.id)
    assert isinstance(response, User)
    assert response.id == user.id
    assert response.name == user.name
    assert response.about == user.about

    updated = await client.users.update(user_id=user.id, **mock_user_update)
    assert updated.name == mock_user_update["name"]
    assert updated.about == mock_user_update["about"]


@test("users: users.get")
def _(client=client, user=test_user):
    response = client.users.get(user.id)

    assert isinstance(response, User)
    assert response.name == mock_user["name"]
    assert response.about == mock_user["about"]


@test("users: users.list empty")
def _(client=client):
    response = client.users.list()
    assert len(response) == 0


@test("users: users.list")
def _(client=client, _=test_user):
    response = client.users.list()
    assert len(response) > 0
    assert isinstance(response[0], User)


@test("users: async users.list")
async def _(client=async_client, _=test_user_async):
    response = await client.users.list()
    assert len(response) > 0
    assert isinstance(response[0], User)


@test("users: users.update")
def _(client=client, user=test_user):
    response = client.users.update(
        user_id=user.id,
        name=mock_user_update["name"],
    )

    assert isinstance(response, User)
    assert hasattr(response, "updated_at")
    assert response.name == mock_user_update["name"]


@test("users: users.update with overwrite")
def _(client=client, user=test_user):
    response = client.users.update(
        user_id=user.id,
        overwrite=True,
        name=mock_user_update["name"],
    )

    assert isinstance(response, User)
    assert hasattr(response, "updated_at")
    assert response.name == mock_user_update["name"]
    assert not response.about


@test("users: users.delete")
def _(client=client, user=test_user):
    response = client.users.delete(
        user_id=user.id,
    )

    assert response is None

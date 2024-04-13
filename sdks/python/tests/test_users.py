from ward import test

from julep.api.types import User

from .fixtures import (
    async_client,
    client,
    mock_user,
    mock_user_update,
    test_user,
)


@test("users.create")
def _(user=test_user):
    assert isinstance(user, User)
    assert hasattr(user, "created_at")
    assert user.name == mock_user["name"]
    assert user.about == mock_user["about"]


@test("async users.create, users.get, users.update & users.delete")
async def _(client=async_client):
    user = await client.users.create(**mock_user)

    assert isinstance(user, User)
    assert hasattr(user, "created_at")
    assert user.name == mock_user["name"]
    assert user.about == mock_user["about"]

    try:
        response = await client.users.get(user.id)
        assert isinstance(response, User)
        assert response.id == user.id
        assert response.name == user.name
        assert response.about == user.about

        updated = await client.users.update(user_id=user.id, **mock_user_update)
        assert updated.name == mock_user_update["name"]
        assert updated.about == mock_user_update["about"]

    finally:
        response = await client.users.delete(user_id=user.id)
        assert response is None


@test("users.get")
def _(client=client, user=test_user):
    response = client.users.get(user.id)

    assert isinstance(response, User)
    assert response.name == mock_user["name"]
    assert response.about == mock_user["about"]


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
def _(client=client, user=test_user):
    response = client.users.update(
        user_id=user.id,
        name=mock_user_update["name"],
    )

    assert isinstance(response, User)
    assert hasattr(response, "updated_at")
    assert response.name == mock_user_update["name"]


@test("users.update with overwrite")
def _(client=client, user=test_user):
    response = client.users.update(
        user_id=user.id,
        overwrite=True,
        **mock_user_update,
    )

    assert isinstance(response, User)
    assert hasattr(response, "updated_at")
    assert response.name == mock_user_update["name"]
    assert response.about == mock_user_update["about"]


@test("users.delete")
def _(client=client, user=test_user):
    response = client.users.delete(
        user_id=user.id,
    )

    assert response is None

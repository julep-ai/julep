# Tests for user routes
from uuid import uuid4

from ward import test

from tests.fixtures import client, make_request, test_user


@test("route: unauthorized should fail")
def _(client=client):
    data = dict(
        name="test user",
        about="test user about",
    )

    response = client.request(
        method="POST",
        url="/users",
        data=data,
    )

    assert response.status_code == 403


@test("route: create user")
def _(make_request=make_request):
    data = dict(
        name="test user",
        about="test user about",
    )

    response = make_request(
        method="POST",
        url="/users",
        json=data,
    )

    assert response.status_code == 201


@test("route: get user not exists")
def _(make_request=make_request):
    user_id = str(uuid4())

    response = make_request(
        method="GET",
        url=f"/users/{user_id}",
    )

    assert response.status_code == 404


@test("route: get user exists")
def _(make_request=make_request, user=test_user):
    user_id = str(user.id)

    response = make_request(
        method="GET",
        url=f"/users/{user_id}",
    )

    assert response.status_code != 404


@test("route: delete user")
def _(make_request=make_request):
    data = dict(
        name="test user",
        about="test user about",
    )

    response = make_request(
        method="POST",
        url="/users",
        json=data,
    )
    user_id = response.json()["id"]

    response = make_request(
        method="DELETE",
        url=f"/users/{user_id}",
    )

    assert response.status_code == 202

    response = make_request(
        method="GET",
        url=f"/users/{user_id}",
    )

    assert response.status_code == 404


@test("route: update user")
def _(make_request=make_request, user=test_user):
    data = dict(
        name="updated user",
        about="updated user about",
    )

    user_id = str(user.id)
    response = make_request(
        method="PUT",
        url=f"/users/{user_id}",
        json=data,
    )

    assert response.status_code == 200

    user_id = response.json()["id"]

    response = make_request(
        method="GET",
        url=f"/users/{user_id}",
    )

    assert response.status_code == 200
    user = response.json()

    assert user["name"] == "updated user"
    assert user["about"] == "updated user about"


@test("model: patch user")
def _(make_request=make_request, user=test_user):
    user_id = str(user.id)

    data = dict(
        name="patched user",
        about="patched user about",
    )

    response = make_request(
        method="PATCH",
        url=f"/users/{user_id}",
        json=data,
    )

    assert response.status_code == 200

    user_id = response.json()["id"]

    response = make_request(
        method="GET",
        url=f"/users/{user_id}",
    )

    assert response.status_code == 200
    user = response.json()

    assert user["name"] == "patched user"
    assert user["about"] == "patched user about"


@test("model: list users")
def _(make_request=make_request):
    response = make_request(
        method="GET",
        url="/users",
    )

    assert response.status_code == 200
    response = response.json()
    users = response["items"]

    assert isinstance(users, list)
    assert len(users) > 0

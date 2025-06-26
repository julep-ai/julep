# Tests for user routes

from uuid_extensions import uuid7
from ward import test

from tests.fixtures import client, make_request, test_project, test_user


@test("route: unauthorized should fail")
def _(client=client):
    data = {
        "name": "test user",
        "about": "test user about",
    }

    response = client.request(
        method="POST",
        url="/users",
        json=data,
    )

    assert response.status_code == 403


@test("route: create user")
def _(make_request=make_request):
    data = {
        "name": "test user",
        "about": "test user about",
    }

    response = make_request(
        method="POST",
        url="/users",
        json=data,
    )

    assert response.status_code == 201


@test("route: create user with project")
def _(make_request=make_request, project=test_project):
    data = {
        "name": "test user with project",
        "about": "test user about",
        "project": project.canonical_name,
    }

    response = make_request(
        method="POST",
        url="/users",
        json=data,
    )

    assert response.status_code == 201
    assert response.json()["project"] == project.canonical_name


@test("route: get user not exists")
def _(make_request=make_request):
    user_id = str(uuid7())

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
    data = {
        "name": "test user",
        "about": "test user about",
    }

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
    data = {
        "name": "updated user",
        "about": "updated user about",
    }

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


@test("route: update user with project")
def _(make_request=make_request, user=test_user, project=test_project):
    data = {
        "name": "updated user with project",
        "about": "updated user about",
        "project": project.canonical_name,
    }

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

    assert user["name"] == "updated user with project"
    assert user["about"] == "updated user about"
    assert user["project"] == project.canonical_name


@test("query: patch user")
def _(make_request=make_request, user=test_user):
    user_id = str(user.id)

    data = {
        "name": "patched user",
        "about": "patched user about",
    }

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


@test("query: patch user with project")
def _(make_request=make_request, user=test_user, project=test_project):
    user_id = str(user.id)

    data = {
        "name": "patched user with project",
        "about": "patched user about",
        "project": project.canonical_name,
    }

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

    assert user["name"] == "patched user with project"
    assert user["about"] == "patched user about"
    assert user["project"] == project.canonical_name


@test("query: list users")
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


@test("query: list users with project filter")
def _(make_request=make_request, project=test_project):
    # First create a user with the project
    data = {
        "name": "test user for project filter",
        "about": "test user about",
        "project": project.canonical_name,
    }

    make_request(
        method="POST",
        url="/users",
        json=data,
    )

    # Then list users with project filter
    response = make_request(
        method="GET",
        url="/users",
        params={
            "project": project.canonical_name,
        },
    )

    assert response.status_code == 200
    response = response.json()
    users = response["items"]

    assert isinstance(users, list)
    assert len(users) > 0
    assert any(user["project"] == project.canonical_name for user in users)


@test("query: list users with right metadata filter")
def _(make_request=make_request, user=test_user):
    response = make_request(
        method="GET",
        url="/users",
        params={
            "metadata_filter": {"test": "test"},
        },
    )

    assert response.status_code == 200
    response = response.json()
    users = response["items"]

    assert isinstance(users, list)
    assert len(users) > 0

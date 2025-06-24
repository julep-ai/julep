from uuid_extensions import uuid7

# Fixtures from conftest.py: client, make_request, test_project, test_user


def test_route_unauthorized_should_fail(client):
    """route: unauthorized should fail"""
    data = {"name": "test user", "about": "test user about"}
    response = client.request(method="POST", url="/users", json=data)
    assert response.status_code == 403


def test_route_create_user(make_request):
    """route: create user"""
    data = {"name": "test user", "about": "test user about"}
    response = make_request(method="POST", url="/users", json=data)
    assert response.status_code == 201


def test_route_create_user_with_project(make_request, test_project):
    """route: create user with project"""
    data = {
        "name": "test user with project",
        "about": "test user about",
        "project": test_project.canonical_name,
    }
    response = make_request(method="POST", url="/users", json=data)
    assert response.status_code == 201
    assert response.json()["project"] == test_project.canonical_name


def test_route_get_user_not_exists(make_request):
    """route: get user not exists"""
    user_id = str(uuid7())
    response = make_request(method="GET", url=f"/users/{user_id}")
    assert response.status_code == 404


def test_route_get_user_exists(make_request, test_user):
    """route: get user exists"""
    user_id = str(test_user.id)
    response = make_request(method="GET", url=f"/users/{user_id}")
    assert response.status_code != 404


def test_route_delete_user(make_request):
    """route: delete user"""
    data = {"name": "test user", "about": "test user about"}
    response = make_request(method="POST", url="/users", json=data)
    user_id = response.json()["id"]
    response = make_request(method="DELETE", url=f"/users/{user_id}")
    assert response.status_code == 202
    response = make_request(method="GET", url=f"/users/{user_id}")
    assert response.status_code == 404


def test_route_update_user(make_request, test_user):
    """route: update user"""
    data = {"name": "updated user", "about": "updated user about"}
    user_id = str(test_user.id)
    response = make_request(method="PUT", url=f"/users/{user_id}", json=data)
    assert response.status_code == 200
    user_id = response.json()["id"]
    response = make_request(method="GET", url=f"/users/{user_id}")
    assert response.status_code == 200
    user = response.json()
    assert user["name"] == "updated user"
    assert user["about"] == "updated user about"


def test_route_update_user_with_project(make_request, test_user, test_project):
    """route: update user with project"""
    data = {
        "name": "updated user with project",
        "about": "updated user about",
        "project": test_project.canonical_name,
    }
    user_id = str(test_user.id)
    response = make_request(method="PUT", url=f"/users/{user_id}", json=data)
    assert response.status_code == 200
    user_id = response.json()["id"]
    response = make_request(method="GET", url=f"/users/{user_id}")
    assert response.status_code == 200
    user = response.json()
    assert user["name"] == "updated user with project"
    assert user["about"] == "updated user about"
    assert user["project"] == test_project.canonical_name


def test_query_patch_user(make_request, test_user):
    """query: patch user"""
    user_id = str(test_user.id)
    data = {"name": "patched user", "about": "patched user about"}
    response = make_request(method="PATCH", url=f"/users/{user_id}", json=data)
    assert response.status_code == 200
    user_id = response.json()["id"]
    response = make_request(method="GET", url=f"/users/{user_id}")
    assert response.status_code == 200
    user = response.json()
    assert user["name"] == "patched user"
    assert user["about"] == "patched user about"


def test_query_patch_user_with_project(make_request, test_user, test_project):
    """query: patch user with project"""
    user_id = str(test_user.id)
    data = {
        "name": "patched user with project",
        "about": "patched user about",
        "project": test_project.canonical_name,
    }
    response = make_request(method="PATCH", url=f"/users/{user_id}", json=data)
    assert response.status_code == 200
    user_id = response.json()["id"]
    response = make_request(method="GET", url=f"/users/{user_id}")
    assert response.status_code == 200
    user = response.json()
    assert user["name"] == "patched user with project"
    assert user["about"] == "patched user about"
    assert user["project"] == test_project.canonical_name


def test_query_list_users(make_request):
    """query: list users"""
    response = make_request(method="GET", url="/users")
    assert response.status_code == 200
    response = response.json()
    users = response["items"]
    assert isinstance(users, list)
    assert len(users) > 0


def test_query_list_users_with_project_filter(make_request, test_project):
    """query: list users with project filter"""
    data = {
        "name": "test user for project filter",
        "about": "test user about",
        "project": test_project.canonical_name,
    }
    make_request(method="POST", url="/users", json=data)
    response = make_request(
        method="GET", url="/users", params={"project": test_project.canonical_name}
    )
    assert response.status_code == 200
    response = response.json()
    users = response["items"]
    assert isinstance(users, list)
    assert len(users) > 0
    assert any(user["project"] == test_project.canonical_name for user in users)


def test_query_list_users_with_right_metadata_filter(make_request, test_user):
    """query: list users with right metadata filter"""
    response = make_request(
        method="GET", url="/users", params={"metadata_filter": {"test": "test"}}
    )
    assert response.status_code == 200
    response = response.json()
    users = response["items"]
    assert isinstance(users, list)
    assert len(users) > 0

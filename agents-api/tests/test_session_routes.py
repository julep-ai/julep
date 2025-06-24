from uuid_extensions import uuid7

# Fixtures from conftest.py: client, make_request, test_agent, test_session


def test_route_unauthorized_should_fail(client):
    """route: unauthorized should fail"""
    response = client.request(method="GET", url="/sessions")
    assert response.status_code == 403


def test_route_create_session(make_request, test_agent):
    """route: create session"""
    data = {
        "agent": str(test_agent.id),
        "situation": "test session about",
        "metadata": {"test": "test"},
        "system_template": "test system template",
    }
    response = make_request(method="POST", url="/sessions", json=data)
    assert response.status_code == 201


def test_route_create_session_invalid_agent(make_request, test_agent):
    """route: create session - invalid agent"""
    data = {"agent": str(uuid7()), "situation": "test session about"}
    response = make_request(method="POST", url="/sessions", json=data)
    assert response.status_code == 400
    assert (
        response.json()["error"]["message"]
        == "The specified participant ID is invalid for the given participant type during create"
    )


def test_route_create_or_update_session_create(make_request, test_agent):
    """route: create or update session - create"""
    session_id = uuid7()
    data = {
        "agent": str(test_agent.id),
        "situation": "test session about",
        "metadata": {"test": "test"},
        "system_template": "test system template",
    }
    response = make_request(method="POST", url=f"/sessions/{session_id}", json=data)
    assert response.status_code == 201


def test_route_create_or_update_session_update(make_request, test_session, test_agent):
    """route: create or update session - update"""
    data = {
        "agent": str(test_agent.id),
        "situation": "test session about",
        "metadata": {"test": "test"},
        "system_template": "test system template",
    }
    response = make_request(
        method="POST", url=f"/sessions/{test_session.id}", json=data
    )
    assert response.status_code == 201, f"{response.json()}"


def test_route_create_or_update_session_invalid_agent(make_request, test_session):
    """route: create or update session - invalid agent"""
    data = {"agent": str(uuid7()), "situation": "test session about"}
    response = make_request(
        method="POST", url=f"/sessions/{test_session.id}", json=data
    )
    assert response.status_code == 400
    assert (
        response.json()["error"]["message"]
        == "The specified participant ID is invalid for the given participant type during create or update"
    )


def test_route_get_session_exists(make_request, test_session):
    """route: get session - exists"""
    response = make_request(method="GET", url=f"/sessions/{test_session.id}")
    assert response.status_code == 200


def test_route_get_session_does_not_exist(make_request):
    """route: get session - does not exist"""
    session_id = uuid7()
    response = make_request(method="GET", url=f"/sessions/{session_id}")
    assert response.status_code == 404


def test_route_list_sessions(make_request, test_session):
    """route: list sessions"""
    response = make_request(method="GET", url="/sessions")
    assert response.status_code == 200
    response = response.json()
    sessions = response["items"]
    assert isinstance(sessions, list)
    assert len(sessions) > 0


def test_route_list_sessions_with_metadata_filter(make_request, test_session):
    """route: list sessions with metadata filter"""
    response = make_request(
        method="GET", url="/sessions", params={"metadata_filter": {"test": "test"}}
    )
    assert response.status_code == 200
    response = response.json()
    sessions = response["items"]
    assert isinstance(sessions, list)
    assert len(sessions) > 0


def test_route_get_session_history(make_request, test_session):
    """route: get session history"""
    response = make_request(method="GET", url=f"/sessions/{test_session.id}/history")
    assert response.status_code == 200
    history = response.json()
    assert history["session_id"] == str(test_session.id)


def test_route_patch_session(make_request, test_session):
    """route: patch session"""
    data = {"situation": "test session about"}
    response = make_request(
        method="PATCH", url=f"/sessions/{test_session.id}", json=data
    )
    assert response.status_code == 200


def test_route_update_session(make_request, test_session):
    """route: update session"""
    data = {"situation": "test session about"}
    response = make_request(method="PUT", url=f"/sessions/{test_session.id}", json=data)
    assert response.status_code == 200


def test_route_delete_session(make_request, test_session):
    """route: delete session"""
    response = make_request(method="DELETE", url=f"/sessions/{test_session.id}")
    assert response.status_code == 202

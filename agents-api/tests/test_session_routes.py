from uuid_extensions import uuid7
import pytest

from tests.fixtures import client, make_request, test_agent, test_session


def test_route_unauthorized_should_fail(client=client):
    """route: unauthorized should fail"""
    response = client.request(
        method="GET",
        url="/sessions",
    )

    assert response.status_code == 403


def test_route_create_session(make_request=make_request, agent=test_agent):
    """route: create session"""
    data = {
        "agent": str(agent.id),
        "situation": "test session about",
        "metadata": {"test": "test"},
        "system_template": "test system template",
    }

    response = make_request(
        method="POST",
        url="/sessions",
        json=data,
    )

    assert response.status_code == 201


def test_route_create_or_update_session_create(make_request=make_request, agent=test_agent):
    """route: create or update session - create"""
    session_id = uuid7()

    data = {
        "agent": str(agent.id),
        "situation": "test session about",
        "metadata": {"test": "test"},
        "system_template": "test system template",
    }

    response = make_request(
        method="POST",
        url=f"/sessions/{session_id}",
        json=data,
    )

    assert response.status_code == 201


def test_route_create_or_update_session_update(make_request=make_request, session=test_session, agent=test_agent):
    """route: create or update session - update"""
    data = {
        "agent": str(agent.id),
        "situation": "test session about",
        "metadata": {"test": "test"},
        "system_template": "test system template",
    }

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}",
        json=data,
    )

    assert response.status_code == 201, f"{response.json()}"


def test_route_get_session_exists(make_request=make_request, session=test_session):
    """route: get session - exists"""
    response = make_request(
        method="GET",
        url=f"/sessions/{session.id}",
    )

    assert response.status_code == 200


def test_route_get_session_does_not_exist(make_request=make_request):
    """route: get session - does not exist"""
    session_id = uuid7()
    response = make_request(
        method="GET",
        url=f"/sessions/{session_id}",
    )

    assert response.status_code == 404


def test_route_list_sessions(make_request=make_request, session=test_session):
    """route: list sessions"""
    response = make_request(
        method="GET",
        url="/sessions",
    )

    assert response.status_code == 200
    response = response.json()
    sessions = response["items"]

    assert isinstance(sessions, list)
    assert len(sessions) > 0


def test_route_list_sessions_with_metadata_filter(make_request=make_request, session=test_session):
    """route: list sessions with metadata filter"""
    response = make_request(
        method="GET",
        url="/sessions",
        params={
            "metadata_filter": {"test": "test"},
        },
    )

    assert response.status_code == 200
    response = response.json()
    sessions = response["items"]

    assert isinstance(sessions, list)
    assert len(sessions) > 0


def test_route_get_session_history(make_request=make_request, session=test_session):
    """route: get session history"""
    response = make_request(
        method="GET",
        url=f"/sessions/{session.id}/history",
    )

    assert response.status_code == 200

    history = response.json()
    assert history["session_id"] == str(session.id)


def test_route_patch_session(make_request=make_request, session=test_session):
    """route: patch session"""
    data = {
        "situation": "test session about",
    }

    response = make_request(
        method="PATCH",
        url=f"/sessions/{session.id}",
        json=data,
    )

    assert response.status_code == 200


def test_route_update_session(make_request=make_request, session=test_session):
    """route: update session"""
    data = {
        "situation": "test session about",
    }

    response = make_request(
        method="PUT",
        url=f"/sessions/{session.id}",
        json=data,
    )

    assert response.status_code == 200


def test_route_delete_session(make_request=make_request, session=test_session):
    """route: delete session"""
    response = make_request(
        method="DELETE",
        url=f"/sessions/{session.id}",
    )

    assert response.status_code == 202

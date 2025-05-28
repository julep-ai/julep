from uuid_extensions import uuid7
from ward import test

from tests.fixtures import client, make_request, test_agent, test_session


@test("route: unauthorized should fail")
def _(client=client):
    response = client.request(
        method="GET",
        url="/sessions",
    )

    assert response.status_code == 403


@test("route: create session")
def _(make_request=make_request, agent=test_agent):
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


@test("route: create session - invalid agent")
def _(make_request=make_request, agent=test_agent):
    data = {
        "agent": str(uuid7()),
        "situation": "test session about",
    }

    response = make_request(
        method="POST",
        url="/sessions",
        json=data,
    )

    assert response.status_code == 400
    assert (
        response.json()["error"]["message"]
        == "The specified participant ID is invalid for the given participant type during create"
    )


@test("route: create or update session - create")
def _(make_request=make_request, agent=test_agent):
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


@test("route: create or update session - update")
def _(make_request=make_request, session=test_session, agent=test_agent):
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


@test("route: create or update session - invalid agent")
def _(make_request=make_request, agent=test_agent, session=test_session):
    data = {
        "agent": str(uuid7()),
        "situation": "test session about",
    }

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}",
        json=data,
    )

    assert response.status_code == 400
    assert (
        response.json()["error"]["message"]
        == "The specified participant ID is invalid for the given participant type during create or update"
    )


@test("route: get session - exists")
def _(make_request=make_request, session=test_session):
    response = make_request(
        method="GET",
        url=f"/sessions/{session.id}",
    )

    assert response.status_code == 200


@test("route: get session - does not exist")
def _(make_request=make_request):
    session_id = uuid7()
    response = make_request(
        method="GET",
        url=f"/sessions/{session_id}",
    )

    assert response.status_code == 404


@test("route: list sessions")
def _(make_request=make_request, session=test_session):
    response = make_request(
        method="GET",
        url="/sessions",
    )

    assert response.status_code == 200
    response = response.json()
    sessions = response["items"]

    assert isinstance(sessions, list)
    assert len(sessions) > 0


@test("route: list sessions with metadata filter")
def _(make_request=make_request, session=test_session):
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


@test("route: get session history")
def _(make_request=make_request, session=test_session):
    response = make_request(
        method="GET",
        url=f"/sessions/{session.id}/history",
    )

    assert response.status_code == 200

    history = response.json()
    assert history["session_id"] == str(session.id)


@test("route: patch session")
def _(make_request=make_request, session=test_session):
    data = {
        "situation": "test session about",
    }

    response = make_request(
        method="PATCH",
        url=f"/sessions/{session.id}",
        json=data,
    )

    assert response.status_code == 200


@test("route: update session")
def _(make_request=make_request, session=test_session):
    data = {
        "situation": "test session about",
    }

    response = make_request(
        method="PUT",
        url=f"/sessions/{session.id}",
        json=data,
    )

    assert response.status_code == 200


@test("route: delete session")
def _(make_request=make_request, session=test_session):
    response = make_request(
        method="DELETE",
        url=f"/sessions/{session.id}",
    )

    assert response.status_code == 202

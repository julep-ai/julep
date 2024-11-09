# Tests for agent queries
from uuid import uuid4

from ward import test

from tests.fixtures import client, make_request, test_agent


@test("route: unauthorized should fail")
def _(client=client):
    data = dict(
        name="test agent",
        about="test agent about",
        model="gpt-4o-mini",
    )

    response = client.request(
        method="POST",
        url="/agents",
        json=data,
    )

    assert response.status_code == 403


@test("route: create agent")
def _(make_request=make_request):
    data = dict(
        name="test agent",
        about="test agent about",
        model="gpt-4o-mini",
    )

    response = make_request(
        method="POST",
        url="/agents",
        json=data,
    )

    assert response.status_code == 201


@test("route: create agent with instructions")
def _(make_request=make_request):
    data = dict(
        name="test agent",
        about="test agent about",
        model="gpt-4o-mini",
        instructions=["test instruction"],
    )

    response = make_request(
        method="POST",
        url="/agents",
        json=data,
    )

    assert response.status_code == 201


@test("route: create or update agent")
def _(make_request=make_request):
    agent_id = str(uuid4())

    data = dict(
        name="test agent",
        about="test agent about",
        model="gpt-4o-mini",
        instructions=["test instruction"],
    )

    response = make_request(
        method="POST",
        url=f"/agents/{agent_id}",
        json=data,
    )

    assert response.status_code == 201


@test("route: get agent not exists")
def _(make_request=make_request):
    agent_id = str(uuid4())

    response = make_request(
        method="GET",
        url=f"/agents/{agent_id}",
    )

    assert response.status_code == 404


@test("route: get agent exists")
def _(make_request=make_request, agent=test_agent):
    agent_id = str(agent.id)

    response = make_request(
        method="GET",
        url=f"/agents/{agent_id}",
    )

    assert response.status_code != 404


@test("route: delete agent")
def _(make_request=make_request):
    data = dict(
        name="test agent",
        about="test agent about",
        model="gpt-4o-mini",
        instructions=["test instruction"],
    )

    response = make_request(
        method="POST",
        url="/agents",
        json=data,
    )
    agent_id = response.json()["id"]

    response = make_request(
        method="DELETE",
        url=f"/agents/{agent_id}",
    )

    assert response.status_code == 202

    response = make_request(
        method="GET",
        url=f"/agents/{agent_id}",
    )

    assert response.status_code == 404


@test("route: update agent")
def _(make_request=make_request, agent=test_agent):
    data = dict(
        name="updated agent",
        about="updated agent about",
        default_settings={"temperature": 1.0},
        model="gpt-4o-mini",
        metadata={"hello": "world"},
    )

    agent_id = str(agent.id)
    response = make_request(
        method="PUT",
        url=f"/agents/{agent_id}",
        json=data,
    )

    assert response.status_code == 200

    agent_id = response.json()["id"]

    response = make_request(
        method="GET",
        url=f"/agents/{agent_id}",
    )

    assert response.status_code == 200
    agent = response.json()

    assert "test" not in agent["metadata"]


@test("route: patch agent")
def _(make_request=make_request, agent=test_agent):
    agent_id = str(agent.id)

    data = dict(
        name="patched agent",
        about="patched agent about",
        default_settings={"temperature": 1.0},
        metadata={"something": "else"},
    )

    response = make_request(
        method="PATCH",
        url=f"/agents/{agent_id}",
        json=data,
    )

    assert response.status_code == 200

    agent_id = response.json()["id"]

    response = make_request(
        method="GET",
        url=f"/agents/{agent_id}",
    )

    assert response.status_code == 200
    agent = response.json()

    assert "hello" in agent["metadata"]


@test("route: list agents")
def _(make_request=make_request):
    response = make_request(
        method="GET",
        url="/agents",
    )

    assert response.status_code == 200
    response = response.json()
    agents = response["items"]

    assert isinstance(agents, list)
    assert len(agents) > 0


@test("route: list agents with metadata filter")
def _(make_request=make_request):
    response = make_request(
        method="GET",
        url="/agents",
        params={
            "metadata_filter": {"test": "test"},
        },
    )

    assert response.status_code == 200
    response = response.json()
    agents = response["items"]

    assert isinstance(agents, list)
    assert len(agents) > 0

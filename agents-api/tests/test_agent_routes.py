# Tests for agent routes

from uuid_extensions import uuid7
from ward import test

from tests.fixtures import client, make_request, test_agent, test_project


@test("route: unauthorized should fail")
def _(client=client):
    data = {
        "name": "test agent",
        "about": "test agent about",
        "model": "gpt-4o-mini",
    }

    response = client.request(
        method="POST",
        url="/agents",
        json=data,
    )

    assert response.status_code == 403


@test("route: create agent")
def _(make_request=make_request):
    data = {
        "name": "test agent",
        "about": "test agent about",
        "model": "gpt-4o-mini",
    }

    response = make_request(
        method="POST",
        url="/agents",
        json=data,
    )

    assert response.status_code == 201


@test("route: create agent with project")
def _(make_request=make_request, project=test_project):
    data = {
        "name": "test agent with project",
        "about": "test agent about",
        "model": "gpt-4o-mini",
        "project": project.canonical_name,
    }

    response = make_request(
        method="POST",
        url="/agents",
        json=data,
    )

    assert response.status_code == 201
    assert response.json()["project"] == project.canonical_name


@test("route: create agent with instructions")
def _(make_request=make_request):
    data = {
        "name": "test agent",
        "about": "test agent about",
        "model": "gpt-4o-mini",
        "instructions": ["test instruction"],
    }

    response = make_request(
        method="POST",
        url="/agents",
        json=data,
    )

    assert response.status_code == 201


@test("route: create or update agent")
def _(make_request=make_request):
    agent_id = str(uuid7())

    data = {
        "name": "test agent",
        "about": "test agent about",
        "model": "gpt-4o-mini",
        "instructions": ["test instruction"],
    }

    response = make_request(
        method="POST",
        url=f"/agents/{agent_id}",
        json=data,
    )

    assert response.status_code == 201


@test("route: create or update agent with project")
def _(make_request=make_request, project=test_project):
    agent_id = str(uuid7())

    data = {
        "name": "test agent with project",
        "about": "test agent about",
        "model": "gpt-4o-mini",
        "instructions": ["test instruction"],
        "project": project.canonical_name,
    }

    response = make_request(
        method="POST",
        url=f"/agents/{agent_id}",
        json=data,
    )

    assert response.status_code == 201
    assert response.json()["project"] == project.canonical_name


@test("route: get agent not exists")
def _(make_request=make_request):
    agent_id = str(uuid7())

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
    data = {
        "name": "test agent",
        "about": "test agent about",
        "model": "gpt-4o-mini",
        "instructions": ["test instruction"],
    }

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
    data = {
        "name": "updated agent",
        "about": "updated agent about",
        "default_settings": {"temperature": 1.0},
        "model": "gpt-4o-mini",
        "metadata": {"hello": "world"},
    }

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


@test("route: update agent with project")
def _(make_request=make_request, agent=test_agent, project=test_project):
    data = {
        "name": "updated agent with project",
        "about": "updated agent about",
        "default_settings": {"temperature": 1.0},
        "model": "gpt-4o-mini",
        "metadata": {"hello": "world"},
        "project": project.canonical_name,
    }

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

    assert agent["project"] == project.canonical_name


@test("route: patch agent")
def _(make_request=make_request, agent=test_agent):
    agent_id = str(agent.id)

    data = {
        "name": "patched agent",
        "about": "patched agent about",
        "default_settings": {"temperature": 1.0},
        "metadata": {"hello": "world"},
    }

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


@test("route: patch agent with project")
def _(make_request=make_request, agent=test_agent, project=test_project):
    agent_id = str(agent.id)

    data = {
        "name": "patched agent with project",
        "about": "patched agent about",
        "default_settings": {"temperature": 1.0},
        "metadata": {"hello": "world"},
        "project": project.canonical_name,
    }

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
    assert agent["project"] == project.canonical_name


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


@test("route: list agents with project filter")
def _(make_request=make_request, project=test_project):
    # First create an agent with the project
    data = {
        "name": "test agent for project filter",
        "about": "test agent about",
        "model": "gpt-4o-mini",
        "project": project.canonical_name,
    }

    make_request(
        method="POST",
        url="/agents",
        json=data,
    )

    # Then list agents with project filter
    response = make_request(
        method="GET",
        url="/agents",
        params={
            "project": project.canonical_name,
        },
    )

    assert response.status_code == 200
    response = response.json()
    agents = response["items"]

    assert isinstance(agents, list)
    assert len(agents) > 0
    assert any(agent["project"] == project.canonical_name for agent in agents)


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

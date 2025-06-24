from uuid_extensions import uuid7

# Fixtures are now defined in conftest.py and automatically available to tests


def test_route_unauthorized_should_fail(client):
    """route: unauthorized should fail"""
    data = {"name": "test agent", "about": "test agent about", "model": "gpt-4o-mini"}
    response = client.request(method="POST", url="/agents", json=data)
    assert response.status_code == 403


def test_route_create_agent(make_request):
    """route: create agent"""
    data = {"name": "test agent", "about": "test agent about", "model": "gpt-4o-mini"}
    response = make_request(method="POST", url="/agents", json=data)
    assert response.status_code == 201


def test_route_create_agent_with_project(make_request, test_project):
    """route: create agent with project"""
    data = {
        "name": "test agent with project",
        "about": "test agent about",
        "model": "gpt-4o-mini",
        "project": test_project.canonical_name,
    }
    response = make_request(method="POST", url="/agents", json=data)
    assert response.status_code == 201
    assert response.json()["project"] == test_project.canonical_name


def test_route_create_agent_with_instructions(make_request):
    """route: create agent with instructions"""
    data = {
        "name": "test agent",
        "about": "test agent about",
        "model": "gpt-4o-mini",
        "instructions": ["test instruction"],
    }
    response = make_request(method="POST", url="/agents", json=data)
    assert response.status_code == 201


def test_route_create_or_update_agent(make_request):
    """route: create or update agent"""
    agent_id = str(uuid7())
    data = {
        "name": "test agent",
        "about": "test agent about",
        "model": "gpt-4o-mini",
        "instructions": ["test instruction"],
    }
    response = make_request(method="POST", url=f"/agents/{agent_id}", json=data)
    assert response.status_code == 201


def test_route_create_or_update_agent_with_project(make_request, test_project):
    """route: create or update agent with project"""
    agent_id = str(uuid7())
    data = {
        "name": "test agent with project",
        "about": "test agent about",
        "model": "gpt-4o-mini",
        "instructions": ["test instruction"],
        "project": test_project.canonical_name,
    }
    response = make_request(method="POST", url=f"/agents/{agent_id}", json=data)
    assert response.status_code == 201
    assert response.json()["project"] == test_project.canonical_name


def test_route_get_agent_not_exists(make_request):
    """route: get agent not exists"""
    agent_id = str(uuid7())
    response = make_request(method="GET", url=f"/agents/{agent_id}")
    assert response.status_code == 404


def test_route_get_agent_exists(make_request, test_agent):
    """route: get agent exists"""
    agent_id = str(test_agent.id)
    response = make_request(method="GET", url=f"/agents/{agent_id}")
    assert response.status_code != 404


def test_route_delete_agent(make_request):
    """route: delete agent"""
    data = {
        "name": "test agent",
        "about": "test agent about",
        "model": "gpt-4o-mini",
        "instructions": ["test instruction"],
    }
    response = make_request(method="POST", url="/agents", json=data)
    agent_id = response.json()["id"]
    response = make_request(method="DELETE", url=f"/agents/{agent_id}")
    assert response.status_code == 202
    response = make_request(method="GET", url=f"/agents/{agent_id}")
    assert response.status_code == 404


def test_route_update_agent(make_request, test_agent):
    """route: update agent"""
    data = {
        "name": "updated agent",
        "about": "updated agent about",
        "default_settings": {"temperature": 1.0},
        "model": "gpt-4o-mini",
        "metadata": {"hello": "world"},
    }
    agent_id = str(test_agent.id)
    response = make_request(method="PUT", url=f"/agents/{agent_id}", json=data)
    assert response.status_code == 200
    agent_id = response.json()["id"]
    response = make_request(method="GET", url=f"/agents/{agent_id}")
    assert response.status_code == 200
    agent = response.json()
    assert "test" not in agent["metadata"]


def test_route_update_agent_with_project(make_request, test_agent, test_project):
    """route: update agent with project"""
    data = {
        "name": "updated agent with project",
        "about": "updated agent about",
        "default_settings": {"temperature": 1.0},
        "model": "gpt-4o-mini",
        "metadata": {"hello": "world"},
        "project": test_project.canonical_name,
    }
    agent_id = str(test_agent.id)
    response = make_request(method="PUT", url=f"/agents/{agent_id}", json=data)
    assert response.status_code == 200
    agent_id = response.json()["id"]
    response = make_request(method="GET", url=f"/agents/{agent_id}")
    assert response.status_code == 200
    agent = response.json()
    assert agent["project"] == test_project.canonical_name


def test_route_patch_agent(make_request, test_agent):
    """route: patch agent"""
    agent_id = str(test_agent.id)
    data = {
        "name": "patched agent",
        "about": "patched agent about",
        "default_settings": {"temperature": 1.0},
        "metadata": {"hello": "world"},
    }
    response = make_request(method="PATCH", url=f"/agents/{agent_id}", json=data)
    assert response.status_code == 200
    agent_id = response.json()["id"]
    response = make_request(method="GET", url=f"/agents/{agent_id}")
    assert response.status_code == 200
    agent = response.json()
    assert "hello" in agent["metadata"]


def test_route_patch_agent_with_project(make_request, test_agent, test_project):
    """route: patch agent with project"""
    agent_id = str(test_agent.id)
    data = {
        "name": "patched agent with project",
        "about": "patched agent about",
        "default_settings": {"temperature": 1.0},
        "metadata": {"hello": "world"},
        "project": test_project.canonical_name,
    }
    response = make_request(method="PATCH", url=f"/agents/{agent_id}", json=data)
    assert response.status_code == 200
    agent_id = response.json()["id"]
    response = make_request(method="GET", url=f"/agents/{agent_id}")
    assert response.status_code == 200
    agent = response.json()
    assert "hello" in agent["metadata"]
    assert agent["project"] == test_project.canonical_name


def test_route_list_agents(make_request):
    """route: list agents"""
    response = make_request(method="GET", url="/agents")
    assert response.status_code == 200
    response = response.json()
    agents = response["items"]
    assert isinstance(agents, list)
    assert len(agents) > 0


def test_route_list_agents_with_project_filter(make_request, test_project):
    """route: list agents with project filter"""
    data = {
        "name": "test agent for project filter",
        "about": "test agent about",
        "model": "gpt-4o-mini",
        "project": test_project.canonical_name,
    }
    make_request(method="POST", url="/agents", json=data)
    response = make_request(
        method="GET", url="/agents", params={"project": test_project.canonical_name}
    )
    assert response.status_code == 200
    response = response.json()
    agents = response["items"]
    assert isinstance(agents, list)
    assert len(agents) > 0
    assert any(agent["project"] == test_project.canonical_name for agent in agents)


def test_route_list_agents_with_metadata_filter(make_request):
    """route: list agents with metadata filter"""
    response = make_request(
        method="GET", url="/agents", params={"metadata_filter": {"test": "test"}}
    )
    assert response.status_code == 200
    response = response.json()
    agents = response["items"]
    assert isinstance(agents, list)
    assert len(agents) > 0

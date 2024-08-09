# Tests for agent queries
from uuid import uuid4

from cozo_migrate.api import apply, init
from pycozo import Client
from ward import test

from agents_api.models import agent
from agents_api.autogen.openapi_model import Agent

MODEL = "julep-ai/samantha-1-turbo"


def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("model: create agent")
def _():
    client = cozo_client()
    agent_id = uuid4()
    developer_id = uuid4()

    agent.create_agent(
        agent_id=agent_id,
        developer_id=developer_id,
        data={
            "model": MODEL,
            "name": "test agent",
            "about": "test agent about",
        },
        client=client,
    )


@test("model: create agent with instructions")
def _():
    client = cozo_client()
    agent_id = uuid4()
    developer_id = uuid4()

    agent.create_agent(
        agent_id=agent_id,
        developer_id=developer_id,
        data={
            "model": MODEL,
            "name": "test agent",
            "about": "test agent about",
            "instructions": ["test instruction"],
        },
        client=client,
    )


@test("model: get agent not exists")
def _():
    client = cozo_client()
    agent_id = uuid4()
    developer_id = uuid4()

    result = agent.get_agent(agent_id=agent_id, developer_id=developer_id, client=client)

    assert result is None


@test("model: get agent exists")
def _():
    client = cozo_client()
    agent_id = uuid4()
    developer_id = uuid4()

    agent.create_agent(
        agent_id=agent_id,
        developer_id=developer_id,
        data={
            "model": MODEL,
            "name": "test agent",
            "about": "test agent about",
            "default_settings": {"temperature": 1.5},
        },
        client=client,
    )

    result = agent.get_agent(agent_id=agent_id, developer_id=developer_id, client=client)

    assert result is not None
    assert isinstance(result, Agent)
    assert result.default_settings.temperature == 1.5


@test("model: delete agent")
def _():
    client = cozo_client()
    agent_id = uuid4()
    developer_id = uuid4()

    # Create the agent
    agent.create_agent(
        agent_id=agent_id,
        developer_id=developer_id,
        data={
            "model": MODEL,
            "name": "test agent",
            "about": "test agent about",
        },
        client=client,
    )

    # Delete the agent
    agent.delete_agent(agent_id=agent_id, developer_id=developer_id, client=client)

    # Check that the agent is deleted
    result = agent.get_agent(agent_id=agent_id, developer_id=developer_id, client=client)

    assert result is None


@test("model: update agent")
def _():
    client = cozo_client()
    agent_id = uuid4()
    developer_id = uuid4()

    agent.create_agent(
        agent_id=agent_id,
        developer_id=developer_id,
        data={
            "model": MODEL,
            "name": "test agent",
            "about": "test agent about",
        },
        client=client,
    )

    result = agent.update_agent(
        agent_id=agent_id,
        developer_id=developer_id,
        data={
            "name": "updated agent",
            "about": "updated agent about",
            "default_settings": {"temperature": 1.5},
        },
        client=client,
    )

    assert result is not None
    assert isinstance(result, Agent)
    assert result.default_settings.temperature == 1.5


@test("model: list agents")
def _():
    """Tests listing all agents associated with a developer in the database. Verifies that the correct list of agents is retrieved."""
    client = cozo_client()
    developer_id = uuid4()

    result = agent.list_agents(developer_id=developer_id, client=client)

    assert isinstance(result, list)
    assert all(isinstance(agent, Agent) for agent in result)

# Tests for agent queries
from uuid import uuid4

from cozo_migrate.api import init, apply
from pycozo import Client
from ward import test

from .create_agent import create_agent_query
from .delete_agent import delete_agent_query
from .get_agent import get_agent_query
from .list_agents import list_agents_query
from .update_agent import update_agent_query


def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("create agent")
def _():
    client = cozo_client()
    agent_id = uuid4()
    developer_id = uuid4()

    query = create_agent_query(
        agent_id=agent_id,
        developer_id=developer_id,
        name="test agent",
        about="test agent about",
    )

    client.run(query)


@test("create agent with instructions")
def _():
    client = cozo_client()
    agent_id = uuid4()
    developer_id = uuid4()

    query = create_agent_query(
        agent_id=agent_id,
        developer_id=developer_id,
        name="test agent",
        about="test agent about",
        instructions=[
            "test instruction",
        ],
    )

    client.run(query)


@test("get agent not exists")
def _():
    client = cozo_client()
    agent_id = uuid4()
    developer_id = uuid4()

    query = get_agent_query(
        agent_id=agent_id,
        developer_id=developer_id,
    )

    result = client.run(query)

    assert len(result["id"]) == 0


@test("get agent exists")
def _():
    client = cozo_client()
    agent_id = uuid4()
    developer_id = uuid4()

    query = create_agent_query(
        agent_id=agent_id,
        developer_id=developer_id,
        name="test agent",
        about="test agent about",
        default_settings={"temperature": 1.5},
    )

    client.run(query)

    query = get_agent_query(
        agent_id=agent_id,
        developer_id=developer_id,
    )

    result = client.run(query)

    assert len(result["id"]) == 1
    assert "temperature" in result["default_settings"][0]
    assert result["default_settings"][0]["temperature"] == 1.5


@test("delete agent")
def _():
    client = cozo_client()
    agent_id = uuid4()
    developer_id = uuid4()

    # Create the agent
    query = create_agent_query(
        agent_id=agent_id,
        developer_id=developer_id,
        name="test agent",
        about="test agent about",
    )

    client.run(query)

    # Delete the agent
    query = delete_agent_query(
        agent_id=agent_id,
        developer_id=developer_id,
    )

    client.run(query)

    # Check that the agent is deleted
    query = get_agent_query(
        agent_id=agent_id,
        developer_id=developer_id,
    )

    result = client.run(query)

    assert len(result["id"]) == 0


@test("update agent")
def _():
    client = cozo_client()
    agent_id = uuid4()
    developer_id = uuid4()

    create_query = create_agent_query(
        agent_id=agent_id,
        developer_id=developer_id,
        name="test agent",
        about="test agent about",
    )

    client.run(create_query)

    update_query = update_agent_query(
        agent_id=agent_id,
        developer_id=developer_id,
        name="updated agent",
        about="updated agent about",
        default_settings={"temperature": 1.5},
    )

    result = client.run(update_query)
    data = result.iloc[0].to_dict()

    assert data["updated_at"] > data["created_at"]


@test("list agents")
def _():
    client = cozo_client()
    developer_id = uuid4()

    query = list_agents_query(
        developer_id=developer_id,
    )

    result = client.run(query)

    assert len(result["id"]) == 0

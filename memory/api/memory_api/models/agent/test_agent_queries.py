# Tests for agent queries
from pycozo import Client
from uuid import uuid4
from ward import test

from .create_agent import create_agent_query
from .get_agent import get_agent_query
from .list_agents import list_agents_query
from .schema import init


def cozo_client():
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)

    return client


@test("create agent")
def _():
    client = cozo_client()
    agent_id = uuid4()

    query = create_agent_query(
        agent_id=agent_id,
        name="test agent",
        about="test agent about",
    )

    client.run(query)


@test("get agent not exists")
def _():
    client = cozo_client()
    agent_id = uuid4()

    query = get_agent_query(
        agent_id=agent_id,
    )

    result = client.run(query)

    assert len(result["agent_id"]) == 0


@test("get agent exists")
def _():
    client = cozo_client()
    agent_id = uuid4()

    query = create_agent_query(
        agent_id=agent_id,
        name="test agent",
        about="test agent about",
    )

    client.run(query)

    query = get_agent_query(
        agent_id=agent_id,
    )

    result = client.run(query)

    assert len(result["agent_id"]) == 1


@test("list agents")
def _():
    client = cozo_client()

    query = list_agents_query()

    result = client.run(query)

    assert len(result["agent_id"]) == 0

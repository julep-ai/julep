# Tests for session queries
from pycozo import Client
from uuid import uuid4
from ward import test

from .create_session import create_session_query
from .get_session import get_session_query
from .list_sessions import list_sessions_query
from .schema import init


def cozo_client():
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)

    return client


@test("create session")
def _():
    client = cozo_client()
    session_id = uuid4()
    agent_id = uuid4()
    user_id = uuid4()
    situation = "test situation"

    query = create_session_query(
        session_id=session_id,
        user_id=user_id,
        agent_id=agent_id,
        situation="test session about",
    )

    result = client.run(query)


@test("get session not exists")
def _():
    client = cozo_client()
    session_id = uuid4()

    query = get_session_query(
        session_id=session_id,
    )

    result = client.run(query)

    assert len(result["session_id"]) == 0


@test("get session exists")
def _():
    client = cozo_client()
    session_id = uuid4()
    agent_id = uuid4()
    user_id = uuid4()
    situation = "test situation"

    query = create_session_query(
        session_id=session_id,
        user_id=user_id,
        agent_id=agent_id,
        situation="test session about",
    )

    client.run(query)

    query = get_session_query(
        session_id=session_id,
    )

    result = client.run(query)

    assert len(result["session_id"]) == 1


@test("list sessions")
def _():
    client = cozo_client()
    session_id = uuid4()

    query = list_sessions_query()

    result = client.run(query)

    assert len(result["session_id"]) == 0

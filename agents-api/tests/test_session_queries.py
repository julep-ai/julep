# Tests for session queries
from uuid import uuid4

from cozo_migrate.api import apply, init
from pycozo import Client
from ward import test

from agents_api.autogen.Sessions import (
    CreateSessionRequest,
    DeleteSessionRequest,
    GetSessionRequest,
    ListSessionsRequest,
)
from agents_api.models.session.create_session import create_session
from agents_api.models.session.delete_session import delete_session
from agents_api.models.session.get_session import get_session
from agents_api.models.session.list_sessions import list_sessions
from agents_api.autogen.openapi_model import Session

MODEL = "julep-ai/samantha-1-turbo"


def cozo_client(migrations_dir: str = "./migrations"):
    # Create a new client for each test
    # and initialize the schema.
    client = Client()

    init(client)
    apply(client, migrations_dir=migrations_dir, all_=True)

    return client


@test("model: create session")
def _():
    client = cozo_client()
    session_id = uuid4()
    agent_id = uuid4()
    user_id = uuid4()
    developer_id = uuid4()

    create_session(
        session_id=session_id,
        developer_id=developer_id,
        data=CreateSessionRequest(
            users=[user_id],
            agents=[agent_id],
            situation="test session about",
        ),
        client=client,
    )


@test("model: create session no user")
def _():
    client = cozo_client()
    session_id = uuid4()
    agent_id = uuid4()
    developer_id = uuid4()

    create_session(
        session_id=session_id,
        developer_id=developer_id,
        data=CreateSessionRequest(
            agents=[agent_id],
            situation="test session about",
        ),
        client=client,
    )


@test("model: get session not exists")
def _():
    client = cozo_client()
    session_id = uuid4()
    developer_id = uuid4()

    try:
        get_session(
            session_id=session_id,
            developer_id=developer_id,
            data=GetSessionRequest(),
            client=client,
        )
    except Exception as e:
        assert str(e) == "Session not found"


@test("model: get session exists")
def _():
    client = cozo_client()
    session_id = uuid4()
    agent_id = uuid4()
    user_id = uuid4()
    developer_id = uuid4()

    create_session(
        session_id=session_id,
        developer_id=developer_id,
        data=CreateSessionRequest(
            users=[user_id],
            agents=[agent_id],
            situation="test session about",
        ),
        client=client,
    )

    result = get_session(
        session_id=session_id,
        developer_id=developer_id,
        data=GetSessionRequest(),
        client=client,
    )

    assert result is not None
    assert isinstance(result, Session)


@test("model: delete session")
def _():
    client = cozo_client()
    session_id = uuid4()
    agent_id = uuid4()
    user_id = uuid4()
    developer_id = uuid4()

    create_session(
        session_id=session_id,
        developer_id=developer_id,
        data=CreateSessionRequest(
            users=[user_id],
            agents=[agent_id],
            situation="test session about",
        ),
        client=client,
    )

    delete_session(
        session_id=session_id,
        developer_id=developer_id,
        data=DeleteSessionRequest(),
        client=client,
    )

    try:
        get_session(
            session_id=session_id,
            developer_id=developer_id,
            data=GetSessionRequest(),
            client=client,
        )
    except Exception as e:
        assert str(e) == "Session not found"


@test("model: list sessions")
def _():
    client = cozo_client()
    developer_id = uuid4()

    result = list_sessions(
        developer_id=developer_id,
        data=ListSessionsRequest(),
        client=client,
    )

    assert isinstance(result, list)
    assert len(result) == 0

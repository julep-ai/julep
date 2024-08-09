# Tests for session queries
from uuid import uuid4

from ward import test

from agents_api.autogen.openapi_model import Session
from agents_api.autogen.Sessions import CreateSessionRequest
from agents_api.models.session.create_session import create_session
from agents_api.models.session.delete_session import delete_session
from agents_api.models.session.get_session import get_session
from agents_api.models.session.list_sessions import list_sessions
from tests.fixtures import (
    cozo_client,
    test_agent,
    test_developer_id,
    test_session,
    test_user,
)

MODEL = "julep-ai/samantha-1-turbo"


@test("model: create session")
def _(
    client=cozo_client, developer_id=test_developer_id, agent=test_agent, user=test_user
):
    create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            users=[user.id],
            agents=[agent.id],
            situation="test session about",
        ),
        client=client,
    )


@test("model: create session no user")
def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
    create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agents=[agent.id],
            situation="test session about",
        ),
        client=client,
    )


@test("model: get session not exists")
def _(client=cozo_client, developer_id=test_developer_id):
    session_id = uuid4()

    try:
        get_session(
            session_id=session_id,
            developer_id=developer_id,
            client=client,
        )
    except Exception:
        pass
    else:
        assert False, "Session should not exist"


@test("model: get session exists")
def _(client=cozo_client, developer_id=test_developer_id, session=test_session):
    result = get_session(
        session_id=session.id,
        developer_id=developer_id,
        client=client,
    )

    assert result is not None
    assert isinstance(result, Session)


@test("model: delete session")
def _(client=cozo_client, developer_id=test_developer_id, agent=test_agent):
    session = create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
        ),
        client=client,
    )

    delete_session(
        session_id=session.id,
        developer_id=developer_id,
        client=client,
    )

    try:
        get_session(
            session_id=session.id,
            developer_id=developer_id,
            client=client,
        )
    except Exception:
        pass

    else:
        assert False, "Session should not exist"


@test("model: list sessions")
def _(client=cozo_client, developer_id=test_developer_id, session=test_session):
    result = list_sessions(
        developer_id=developer_id,
        client=client,
    )

    assert isinstance(result, list)
    assert len(result) > 0

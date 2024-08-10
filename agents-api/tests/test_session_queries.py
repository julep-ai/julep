# Tests for session queries
from uuid import uuid4

from ward import test

from agents_api.autogen.openapi_model import CreateOrUpdateSessionRequest, Session
from agents_api.autogen.Sessions import CreateSessionRequest
from agents_api.common.protocol.sessions import ChatContext
from agents_api.models.session.create_or_update_session import create_or_update_session
from agents_api.models.session.create_session import create_session
from agents_api.models.session.delete_session import delete_session
from agents_api.models.session.get_session import get_session
from agents_api.models.session.list_sessions import list_sessions
from agents_api.models.session.prepare_chat_context import prepare_chat_context
from tests.fixtures import (
    cozo_client,
    test_agent,
    test_developer_id,
    test_session,
    test_tool,
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


@test("model: create or update session")
def _(
    client=cozo_client, developer_id=test_developer_id, agent=test_agent, user=test_user
):
    session_id = uuid4()

    create_or_update_session(
        session_id=session_id,
        developer_id=developer_id,
        data=CreateOrUpdateSessionRequest(
            users=[user.id],
            agents=[agent.id],
            situation="test session about",
        ),
        client=client,
    )

    result = get_session(
        session_id=session_id,
        developer_id=developer_id,
        client=client,
    )

    assert result is not None
    assert isinstance(result, Session)
    assert result.id == session_id


@test("model: prepare chat context")
def _(
    client=cozo_client,
    developer_id=test_developer_id,
    agent=test_agent,
    session=test_session,
    tool=test_tool,
    user=test_user,
):
    try:
        context = prepare_chat_context(
            developer_id=developer_id,
            session_id=session.id,
            client=client,
        )
    except Exception as e:
        print(repr(e.__cause__))
        raise

    assert isinstance(context, ChatContext)
    assert len(context.entries) > 0
    assert len(context.toolsets) > 0

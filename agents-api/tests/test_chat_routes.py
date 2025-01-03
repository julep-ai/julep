# Tests for session queries

from agents_api.autogen.openapi_model import ChatInput, CreateSessionRequest
from agents_api.clients import litellm
from agents_api.clients.pg import create_db_pool
from agents_api.common.protocol.sessions import ChatContext
from agents_api.queries.chat.gather_messages import gather_messages
from agents_api.queries.chat.prepare_chat_context import prepare_chat_context
from agents_api.queries.sessions.create_session import create_session
from ward import test

from tests.fixtures import (
    make_request,
    patch_embed_acompletion,
    pg_dsn,
    test_agent,
    test_developer,
    test_developer_id,
    test_session,
    test_tool,
    test_user,
)


@test("chat: check that patching libs works")
async def _(
    _=patch_embed_acompletion,
):
    assert (await litellm.acompletion(model="gpt-4o-mini", messages=[])).id == "fake_id"
    assert (await litellm.aembedding())[0][0] == 1.0  # pytype: disable=missing-parameter


@test("chat: check that non-recall gather_messages works")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    session=test_session,
    tool=test_tool,
    user=test_user,
    mocks=patch_embed_acompletion,
):
    (embed, _) = mocks

    pool = await create_db_pool(dsn=dsn)
    chat_context = await prepare_chat_context(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )

    session_id = session.id

    messages = [{"role": "user", "content": "hello"}]

    past_messages, doc_references = await gather_messages(
        developer=developer,
        session_id=session_id,
        chat_context=chat_context,
        chat_input=ChatInput(messages=messages, recall=False),
        connection_pool=pool,
    )

    assert isinstance(past_messages, list)
    assert len(past_messages) >= 0
    assert isinstance(doc_references, list)
    assert len(doc_references) == 0

    # Check that embed was not called
    embed.assert_not_called()


@test("chat: check that gather_messages works")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    # session=test_session,
    tool=test_tool,
    user=test_user,
    mocks=patch_embed_acompletion,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "text",
                "num_search_messages": 10,
                "max_query_length": 1001,
            },
        ),
        connection_pool=pool,
    )

    (embed, _) = mocks

    chat_context = await prepare_chat_context(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )

    session_id = session.id

    messages = [{"role": "user", "content": "hello"}]

    past_messages, doc_references = await gather_messages(
        developer=developer,
        session_id=session_id,
        chat_context=chat_context,
        chat_input=ChatInput(messages=messages, recall=True),
        connection_pool=pool,
    )

    assert isinstance(past_messages, list)
    assert isinstance(doc_references, list)


@test("chat: check that chat route calls both mocks")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=patch_embed_acompletion,
    dsn=pg_dsn,
):
    pool = await create_db_pool(dsn=dsn)
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            recall_options={
                "mode": "vector",
                "num_search_messages": 5,
                "max_query_length": 1001,
            },
        ),
        connection_pool=pool,
    )

    (embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    response.raise_for_status()

    # Check that both mocks were called at least once
    embed.assert_called()
    acompletion.assert_called()


@test("query: prepare chat context")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
    session=test_session,
    tool=test_tool,
    user=test_user,
):
    pool = await create_db_pool(dsn=dsn)
    context = await prepare_chat_context(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )

    assert isinstance(context, ChatContext)
    assert len(context.toolsets) > 0

# Tests for session queries

from agents_api.autogen.openapi_model import ChatInput, CreateAgentRequest, CreateSessionRequest
from agents_api.clients import litellm
from agents_api.clients.pg import create_db_pool
from agents_api.common.protocol.sessions import ChatContext
from agents_api.queries.agents import create_agent
from agents_api.queries.chat.gather_messages import gather_messages
from agents_api.queries.chat.prepare_chat_context import prepare_chat_context
from agents_api.queries.sessions.create_session import create_session
from ward import test

from .fixtures import (
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
                "mode": "hybrid",
                "num_search_messages": 6,
                "max_query_length": 800,
                "confidence": 0.6,
                "limit": 10,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (embed, acompletion) = mocks

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

    embed.assert_called_once()
    acompletion.assert_not_called()


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
                "mode": "hybrid",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
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

    embed.assert_called_once()
    acompletion.assert_called_once()


@test("chat: check that render route works and does not call completion mock")
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
                "mode": "hybrid",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
            },
        ),
        connection_pool=pool,
    )

    (embed, acompletion) = mocks

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/render",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    response.raise_for_status()

    data = response.json()
    messages = data["messages"]
    assert "docs" in data
    assert "tools" in data

    assert len(messages) > 0
    assert messages[0]["role"] == "system"

    embed.assert_called_once()
    acompletion.assert_not_called()


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


@test("chat: test system template merging logic")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    dsn=pg_dsn,
    mocks=patch_embed_acompletion,
):
    """Test that the system template merging logic works correctly.

    - If agent.default_system_template is set and session.system_template is not set,
      use the agent's default template.
    - If session.system_template is set (regardless of whether agent.default_system_template is set),
      use the session's template.
    """
    pool = await create_db_pool(dsn=dsn)

    # Create an agent with a default system template
    agent_default_template = "This is the agent's default system template"
    agent_data = CreateAgentRequest(
        name="test agent with template",
        about="test agent about",
        model="gpt-4o-mini",
        default_system_template=agent_default_template,
    )

    agent = await create_agent(
        developer_id=developer_id,
        data=agent_data,
        connection_pool=pool,
    )

    # Create a session without a system template (should use agent's default)
    session1_data = CreateSessionRequest(
        agent=agent.id,
        situation="test session without template",
    )

    session1 = await create_session(
        developer_id=developer_id,
        data=session1_data,
        connection_pool=pool,
    )

    # Create a session with a system template (should override agent's default)
    session_template = "This is the session's system template"
    session2_data = CreateSessionRequest(
        agent=agent.id,
        situation="test session with template",
        system_template=session_template,
    )

    session2 = await create_session(
        developer_id=developer_id,
        data=session2_data,
        connection_pool=pool,
    )

    # Test session without system template (should use agent's default)
    response1 = make_request(
        method="POST",
        url=f"/sessions/{session1.id}/render",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    response1.raise_for_status()
    data1 = response1.json()
    messages1 = data1["messages"]

    # Verify first message is system message with agent's default template
    assert len(messages1) > 0
    assert messages1[0]["role"] == "system"
    assert "You are test agent with template" in messages1[0]["content"]
    assert "About you: test agent about" in messages1[0]["content"]

    # Test session with system template (should override agent's default)
    response2 = make_request(
        method="POST",
        url=f"/sessions/{session2.id}/render",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    response2.raise_for_status()
    data2 = response2.json()
    messages2 = data2["messages"]

    # Verify first message is system message with session's template
    assert len(messages2) > 0
    assert messages2[0]["role"] == "system"
    assert session_template in messages2[0]["content"]
    assert agent_default_template not in messages2[0]["content"]

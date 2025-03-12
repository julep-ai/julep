# Tests for session queries

from agents_api.autogen.openapi_model import (
    ChatInput,
    CreateAgentRequest,
    CreateSessionRequest,
    VectorDocSearch,
)
from agents_api.clients import litellm
from agents_api.clients.pg import create_db_pool
from agents_api.common.protocol.sessions import ChatContext
from agents_api.queries.agents.create_agent import create_agent
from agents_api.queries.chat.gather_messages import gather_messages
from agents_api.queries.chat.prepare_chat_context import prepare_chat_context
from agents_api.queries.sessions.create_session import create_session
from litellm.types.utils import ModelResponse
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


@test("chat: check that streaming chat route works")
async def _(
    make_request=make_request,
    developer_id=test_developer_id,
    agent=test_agent,
    mocks=patch_embed_acompletion,
    dsn=pg_dsn,
):
    (embed, acompletion) = mocks

    # Configure mock acompletion to behave like a streaming response
    mock_chunk_iter = [
        ModelResponse(
            id="fake_id",
            choices=[
                {
                    "delta": {"content": "Hello, ", "role": "assistant"},
                    "created_at": 1,
                },
            ],
            created=0,
            object="text_completion_chunk",
        ),
        ModelResponse(
            id="fake_id",
            choices=[
                {
                    "delta": {"content": "world!", "role": "assistant"},
                    "created_at": 1,
                    "finish_reason": "stop",
                },
            ],
            created=0,
            object="text_completion_chunk",
            usage={"total_tokens": 10, "prompt_tokens": 5, "completion_tokens": 5},
        ),
    ]

    # Set up the mock to return an async iterator
    async def mock_response():
        for chunk in mock_chunk_iter:
            yield chunk

    acompletion.return_value = mock_response()

    pool = await create_db_pool(dsn=dsn)

    # Create the session using the existing agent fixture
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test streaming session",
        ),
        connection_pool=pool,
    )

    # Make the request with stream=True
    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={
            "messages": [{"role": "user", "content": "hello"}],
            "stream": True,
        },
    )

    # Verify response
    assert response.status_code in (200, 201)  # Accept either success code
    assert response.headers.get("content-type") == "application/json"

    # Process streaming response
    content = response.content.decode("utf-8")
    chunks = [line for line in content.split("\n") if line.strip()]

    # Verify we got chunks
    assert len(chunks) >= 2  # We should have at least 2 chunks

    # Check that we got embed and acompletion calls
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
    agent_default_template = (
        "This is the agent's default system template {{agent.name.upper()}}"
    )
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
    session_template = "This is the session's system template: {{session.situation.upper()}}"
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

    # Test session with system template (should override agent's default)
    response2 = make_request(
        method="POST",
        url=f"/sessions/{session2.id}/render",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    response2.raise_for_status()
    data2 = response2.json()
    messages2 = data2["messages"]

    # Verify messages with session's template
    assert len(messages2) > 0
    assert messages2[0]["role"] == "system"
    assert (
        session2_data.situation.upper()
        in messages2[0]["content"]  # pytype: disable=attribute-error
    )

    # Verify messages with agent's default template
    assert len(messages1) > 0
    assert messages1[0]["role"] == "system"
    assert agent_data.name.upper() in messages1[0]["content"]


@test("chat: validate the recall options for different modes in chat context")
async def _(agent=test_agent, dsn=pg_dsn, developer_id=test_developer_id):
    pool = await create_db_pool(dsn=dsn)

    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session about",
            system_template="test system template",
        ),
        connection_pool=pool,
    )

    chat_context = await prepare_chat_context(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )

    assert chat_context.session.recall_options == VectorDocSearch(
        mode="vector",
        num_search_messages=4,
        max_query_length=1000,
        limit=10,
        lang="en-US",
    )

    # Create a session with a hybrid recall options to hybrid mode
    data = CreateSessionRequest(
        agent=agent.id,
        situation="test session about",
        system_template="test system template",
        recall_options={
            "mode": "hybrid",
            "num_search_messages": 6,
            "max_query_length": 800,
            "confidence": 0.6,
            "limit": 10,
            "mmr_strength": 0.5,
            "lang": "en-US",
            "alpha": 0.75,
            "metadata_filter": {"hybridsearch": "hybridsearch"},
        },
    )

    session = await create_session(
        developer_id=developer_id,
        data=data,
        connection_pool=pool,
    )

    # assert session.recall_options == data.recall_options
    chat_context = await prepare_chat_context(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )

    assert chat_context.session.recall_options.mode == data.recall_options.mode
    assert (
        chat_context.session.recall_options.num_search_messages
        == data.recall_options.num_search_messages
    )
    assert (
        chat_context.session.recall_options.max_query_length
        == data.recall_options.max_query_length
    )
    assert chat_context.session.recall_options.limit == data.recall_options.limit
    assert chat_context.session.recall_options.lang == data.recall_options.lang
    assert (
        chat_context.session.recall_options.metadata_filter
        == data.recall_options.metadata_filter
    )

    # Update session to have a new recall options to text mode
    data = CreateSessionRequest(
        agent=agent.id,
        situation="test session about",
        system_template="test system template",
        recall_options={
            "mode": "text",
            "num_search_messages": 6,
            "max_query_length": 800,
            "metadata_filter": {"textsearch": "textsearch"},
            "limit": 10,
            "lang": "en-US",
        },
    )

    session = await create_session(
        developer_id=developer_id,
        data=data,
        connection_pool=pool,
    )

    # assert session.recall_options == data.recall_options
    chat_context = await prepare_chat_context(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )

    assert chat_context.session.recall_options.mode == data.recall_options.mode
    assert (
        chat_context.session.recall_options.num_search_messages
        == data.recall_options.num_search_messages
    )
    assert (
        chat_context.session.recall_options.max_query_length
        == data.recall_options.max_query_length
    )
    assert chat_context.session.recall_options.limit == data.recall_options.limit
    assert chat_context.session.recall_options.lang == data.recall_options.lang
    assert (
        chat_context.session.recall_options.metadata_filter
        == data.recall_options.metadata_filter
    )

    # Update session to have a new recall options to vector mode
    data = CreateSessionRequest(
        agent=agent.id,
        situation="test session about",
        system_template="test system template",
        recall_options={
            "mode": "vector",
            "num_search_messages": 6,
            "max_query_length": 800,
            "limit": 10,
            "lang": "en-US",
            "metadata_filter": {"vectorsearch": "vectorsearch"},
            "confidence": 0.6,
        },
    )

    session = await create_session(
        developer_id=developer_id,
        data=data,
        connection_pool=pool,
    )

    # assert session.recall_options == data.recall_options
    chat_context = await prepare_chat_context(
        developer_id=developer_id,
        session_id=session.id,
        connection_pool=pool,
    )

    assert chat_context.session.recall_options.mode == data.recall_options.mode
    assert (
        chat_context.session.recall_options.num_search_messages
        == data.recall_options.num_search_messages
    )
    assert (
        chat_context.session.recall_options.max_query_length
        == data.recall_options.max_query_length
    )
    assert chat_context.session.recall_options.limit == data.recall_options.limit
    assert chat_context.session.recall_options.lang == data.recall_options.lang
    assert (
        chat_context.session.recall_options.metadata_filter
        == data.recall_options.metadata_filter
    )
    assert chat_context.session.recall_options.confidence == data.recall_options.confidence
    assert chat_context.session.recall_options.mmr_strength == 0.5

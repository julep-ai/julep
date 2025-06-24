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


async def test_chat_check_that_patching_libs_works(patch_embed_acompletion):
    """chat: check that patching libs works"""
    assert (await litellm.acompletion(model="gpt-4o-mini", messages=[])).id == "fake_id"
    assert (await litellm.aembedding())[0][0] == 1.0  # pytype: disable=missing-parameter


async def test_chat_check_that_non_recall_gather_messages_works(
    test_developer,
    pg_dsn,
    test_developer_id,
    test_agent,
    test_session,
    test_tool,
    test_user,
    patch_embed_acompletion,
):
    """chat: check that non-recall gather_messages works"""
    embed, _ = patch_embed_acompletion

    pool = await create_db_pool(dsn=pg_dsn)
    chat_context = await prepare_chat_context(
        developer_id=test_developer_id,
        session_id=test_session.id,
        connection_pool=pool,
    )

    session_id = test_session.id

    messages = [{"role": "user", "content": "hello"}]

    past_messages, doc_references = await gather_messages(
        developer=test_developer,
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


async def test_chat_check_that_gather_messages_works(
    test_developer,
    pg_dsn,
    test_developer_id,
    test_agent,
    test_tool,
    test_user,
    patch_embed_acompletion,
):
    """chat: check that gather_messages works"""
    pool = await create_db_pool(dsn=pg_dsn)
    session = await create_session(
        developer_id=test_developer_id,
        data=CreateSessionRequest(
            agent=test_agent.id,
            situation="test session about",
        ),
        connection_pool=pool,
    )

    embed, acompletion = patch_embed_acompletion

    chat_context = await prepare_chat_context(
        developer_id=test_developer_id,
        session_id=session.id,
        connection_pool=pool,
    )

    session_id = session.id

    messages = [{"role": "user", "content": "hello"}]

    past_messages, doc_references = await gather_messages(
        developer=test_developer,
        session_id=session_id,
        chat_context=chat_context,
        chat_input=ChatInput(messages=messages, recall=True),
        connection_pool=pool,
    )

    assert isinstance(past_messages, list)
    assert isinstance(doc_references, list)

    embed.assert_called_once()
    acompletion.assert_not_called()


async def test_chat_check_that_chat_route_calls_both_mocks(
    make_request,
    test_developer_id,
    test_agent,
    patch_embed_acompletion,
    pg_dsn,
):
    """chat: check that chat route calls both mocks"""
    pool = await create_db_pool(dsn=pg_dsn)
    session = await create_session(
        developer_id=test_developer_id,
        data=CreateSessionRequest(
            agent=test_agent.id,
            situation="test session about",
            recall_options={
                "mode": "hybrid",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
                "trigram_similarity_threshold": 0.4,
                "k_multiplier": 7,
            },
        ),
        connection_pool=pool,
    )

    embed, acompletion = patch_embed_acompletion

    response = make_request(
        method="POST",
        url=f"/sessions/{session.id}/chat",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    response.raise_for_status()

    embed.assert_called_once()
    acompletion.assert_called_once()


async def test_chat_check_that_render_route_works_and_does_not_call_completion_mock(
    make_request,
    test_developer_id,
    test_agent,
    patch_embed_acompletion,
    pg_dsn,
):
    """chat: check that render route works and does not call completion mock"""
    pool = await create_db_pool(dsn=pg_dsn)
    session = await create_session(
        developer_id=test_developer_id,
        data=CreateSessionRequest(
            agent=test_agent.id,
            situation="test session about",
            recall_options={
                "mode": "hybrid",
                "num_search_messages": 10,
                "max_query_length": 1001,
                "confidence": 0.6,
                "limit": 5,
                "mmr_strength": 0.5,
                "trigram_similarity_threshold": 0.4,
                "k_multiplier": 7,
            },
        ),
        connection_pool=pool,
    )

    embed, acompletion = patch_embed_acompletion

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


async def test_query_prepare_chat_context(
    pg_dsn,
    test_developer_id,
    test_agent,
    test_session,
    test_tool,
    test_user,
):
    """query: prepare chat context"""
    pool = await create_db_pool(dsn=pg_dsn)
    context = await prepare_chat_context(
        developer_id=test_developer_id,
        session_id=test_session.id,
        connection_pool=pool,
    )

    assert isinstance(context, ChatContext)
    assert len(context.toolsets) > 0


async def test_chat_test_system_template_merging_logic(
    make_request,
    test_developer_id,
    pg_dsn,
    patch_embed_acompletion,
):
    """Test that the system template merging logic works correctly.

    - If agent.default_system_template is set and session.system_template is not set,
      use the agent's default template.
    - If session.system_template is set (regardless of whether agent.default_system_template is set),
      use the session's template.
    """
    pool = await create_db_pool(dsn=pg_dsn)

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
        developer_id=test_developer_id,
        data=agent_data,
        connection_pool=pool,
    )

    # Create a session without a system template (should use agent's default)
    session1_data = CreateSessionRequest(
        agent=agent.id,
        situation="test session without template",
    )

    session1 = await create_session(
        developer_id=test_developer_id,
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
        developer_id=test_developer_id,
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


async def test_chat_validate_the_recall_options_for_different_modes_in_chat_context(
    test_agent, pg_dsn, test_developer_id
):
    """chat: validate the recall options for different modes in chat context"""
    pool = await create_db_pool(dsn=pg_dsn)

    session = await create_session(
        developer_id=test_developer_id,
        data=CreateSessionRequest(
            agent=test_agent.id,
            situation="test session about",
            system_template="test system template",
        ),
        connection_pool=pool,
    )

    chat_context = await prepare_chat_context(
        developer_id=test_developer_id,
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
        agent=test_agent.id,
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
            "trigram_similarity_threshold": 0.4,
            "k_multiplier": 7,
        },
    )

    session = await create_session(
        developer_id=test_developer_id,
        data=data,
        connection_pool=pool,
    )

    # assert session.recall_options == data.recall_options
    chat_context = await prepare_chat_context(
        developer_id=test_developer_id,
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
    assert (
        chat_context.session.recall_options.trigram_similarity_threshold
        == data.recall_options.trigram_similarity_threshold
    )
    assert chat_context.session.recall_options.k_multiplier == data.recall_options.k_multiplier

    # Update session to have a new recall options to text mode
    data = CreateSessionRequest(
        agent=test_agent.id,
        situation="test session about",
        system_template="test system template",
        recall_options={
            "mode": "text",
            "num_search_messages": 6,
            "max_query_length": 800,
            "metadata_filter": {"textsearch": "textsearch"},
            "limit": 10,
            "lang": "en-US",
            "trigram_similarity_threshold": 0.4,
        },
    )

    session = await create_session(
        developer_id=test_developer_id,
        data=data,
        connection_pool=pool,
    )

    # assert session.recall_options == data.recall_options
    chat_context = await prepare_chat_context(
        developer_id=test_developer_id,
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
    assert (
        chat_context.session.recall_options.trigram_similarity_threshold
        == data.recall_options.trigram_similarity_threshold
    )

    # Update session to have a new recall options to vector mode
    data = CreateSessionRequest(
        agent=test_agent.id,
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
        developer_id=test_developer_id,
        data=data,
        connection_pool=pool,
    )

    # assert session.recall_options == data.recall_options
    chat_context = await prepare_chat_context(
        developer_id=test_developer_id,
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

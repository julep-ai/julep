"""Tests for the streaming logic in the chat function."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from agents_api.autogen.openapi_model import (
    ChatInput,
    CreateSessionRequest,
    DocReference,
)
from agents_api.clients.pg import create_db_pool
from agents_api.queries.sessions.create_session import create_session
from agents_api.routers.sessions.legacy.chat import _join_deltas, chat
from fastapi import BackgroundTasks
from starlette.responses import StreamingResponse
from uuid_extensions import uuid7
from ward import skip, test

from .fixtures import (
    pg_dsn,
    test_agent,
    test_developer,
    test_developer_id,
)


async def get_usage_records(dsn: str, developer_id: str, limit: int = 100):
    """Helper function to get usage records for testing."""
    pool = await create_db_pool(dsn=dsn)

    records = await pool.fetch(
        """
        SELECT
            developer_id,
            model,
            prompt_tokens,
            completion_tokens,
            cost,
            estimated,
            custom_api_used,
            created_at,
            metadata
        FROM usage
        WHERE developer_id = $1
        ORDER BY created_at DESC
        LIMIT $2;""",
        developer_id,
        limit,
    )

    # Convert records to dictionaries
    return [dict(record) for record in records]


async def delete_usage_records(dsn: str, developer_id: str):
    """Helper function to delete usage records for testing."""
    pool = await create_db_pool(dsn=dsn)

    await pool.execute(
        """
        DELETE FROM usage
        WHERE developer_id = $1
        """,
        developer_id,
    )


async def collect_stream_content(response: StreamingResponse) -> list[dict]:
    """Helper function to collect stream chunks in a list."""
    chunks = []
    async for chunk in response.body_iterator:
        # Ensure we're dealing with string data
        if isinstance(chunk, bytes):
            chunk = chunk.decode("utf-8")

        # Handle SSE format: data: {JSON}\n\n
        if chunk.startswith("data: "):
            json_data = chunk[6:].strip()  # Remove 'data: ' prefix and whitespace
            if json_data:  # Only parse non-empty data
                chunks.append(json.loads(json_data))
        else:
            # Fallback for raw JSON (for backward compatibility)
            chunk = chunk.strip()
            if chunk:
                chunks.append(json.loads(chunk))
    return chunks


@test("join_deltas: Test correct behavior")
async def _():
    """Test that join_deltas works properly to merge deltas."""
    # Test initial case where content needs to be added
    acc = {"content": ""}
    delta = {"content": "Hello", "role": "assistant"}
    result = _join_deltas(acc, delta)
    assert result == {"content": "Hello", "role": "assistant"}

    # Test appending content
    acc = {"content": "Hello"}
    delta = {"content": " world!", "role": "assistant"}
    result = _join_deltas(acc, delta)
    assert result == {"content": "Hello world!", "role": "assistant"}

    # Test with no content in delta
    acc = {"content": "Hello world!"}
    delta = {"finish_reason": "stop"}
    result = _join_deltas(acc, delta)
    assert result == {"content": "Hello world!", "finish_reason": "stop"}

    # Test with None content
    acc = {"content": None}
    delta = {"content": "Hello", "role": "assistant"}
    result = _join_deltas(acc, delta)
    assert result == {"content": "Hello", "role": "assistant"}

    # Test with None content in delta
    acc = {"content": "Hello"}
    delta = {"content": None, "role": "assistant"}
    result = _join_deltas(acc, delta)
    assert result == {"content": "Hello", "role": "assistant"}


@test("chat: Test streaming response format")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that streaming responses follow the correct format."""
    pool = await create_db_pool(dsn=dsn)

    # Create a session
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session for streaming format",
        ),
        connection_pool=pool,
    )

    # Mock render_chat_input to return consistent values
    async def mock_render(*args, **kwargs):
        return (
            [{"role": "user", "content": "Hello"}],  # messages
            [],  # doc_references
            None,  # formatted_tools
            {"model": "gpt-4o-mini"},  # settings
            [{"role": "user", "content": "Hello"}],  # new_messages
            MagicMock(),  # chat_context
        )

    with patch(
        "agents_api.routers.sessions.legacy.chat.render_chat_input", side_effect=mock_render
    ):
        # Create chat input with stream=True
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
        )

        # Call the chat function with mock response that includes finish_reason
        mock_response = "This is a test response"
        response = await chat(
            developer=developer,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=BackgroundTasks(),
            mock_response=mock_response,
            connection_pool=pool,
        )

        # Verify response type is StreamingResponse
        assert isinstance(response, StreamingResponse)
        assert response.media_type == "text/event-stream"

        # Collect and parse stream content
        parsed_chunks = await collect_stream_content(response)

        assert len(parsed_chunks) > 0

        resulting_content = []

        # Verify chunk format
        for chunk in parsed_chunks:
            assert "id" in chunk
            assert "created_at" in chunk
            assert "choices" in chunk
            assert isinstance(chunk["choices"], list)
            for choice in chunk["choices"]:
                resulting_content.append(choice["delta"]["content"] or "")
                assert "delta" in choice
                assert "content" in choice["delta"]
                assert "finish_reason" in choice
                assert choice["finish_reason"] in [
                    "stop",
                    "length",
                    "content_filter",
                    "tool_calls",
                ]

        assert "".join(resulting_content) == mock_response


@test("chat: Test streaming with document references")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that document references are included in streaming response."""
    pool = await create_db_pool(dsn=dsn)

    # Create a session
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session for streaming with documents",
        ),
        connection_pool=pool,
    )

    # Create document references with required fields
    doc_refs = [
        DocReference(
            id=str(uuid7()),
            title="Test Document 1",
            owner={"id": developer_id, "role": "user"},
            snippet={"index": 0, "content": "Test snippet 1"},
        ),
        DocReference(
            id=str(uuid7()),
            title="Test Document 2",
            owner={"id": developer_id, "role": "user"},
            snippet={"index": 0, "content": "Test snippet 2"},
        ),
    ]

    # Mock render_chat_input to return document references
    async def mock_render(*args, **kwargs):
        return (
            [{"role": "user", "content": "Hello"}],  # messages
            doc_refs,  # doc_references
            None,  # formatted_tools
            {"model": "gpt-4o-mini"},  # settings
            [{"role": "user", "content": "Hello"}],  # new_messages
            MagicMock(),  # chat_context
        )

    with patch(
        "agents_api.routers.sessions.legacy.chat.render_chat_input", side_effect=mock_render
    ):
        # Create chat input with stream=True
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
        )

        # Call the chat function with mock response that includes finish_reason
        mock_response = "This is a test response"
        response = await chat(
            developer=developer,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=BackgroundTasks(),
            mock_response=mock_response,
            connection_pool=pool,
        )

        # Collect and parse stream content
        parsed_chunks = await collect_stream_content(response)

        # Verify document references in chunks
        for chunk in parsed_chunks:
            assert "docs" in chunk
            assert len(chunk["docs"]) == len(doc_refs)
            for doc_ref in chunk["docs"]:
                assert "id" in doc_ref
                assert "title" in doc_ref
                assert "owner" in doc_ref
                assert "snippet" in doc_ref


@skip("Skipping message history saving test")
@test("chat: Test streaming with message history saving")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that messages are saved to history when streaming with save=True."""
    pool = await create_db_pool(dsn=dsn)

    # Create a session
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session for streaming with history",
        ),
        connection_pool=pool,
    )

    # Mock render_chat_input to return consistent values
    async def mock_render(*args, **kwargs):
        return (
            [{"role": "user", "content": "Hello"}],  # messages
            [],  # doc_references
            None,  # formatted_tools
            {"model": "gpt-4o-mini"},  # settings
            [{"role": "user", "content": "Hello"}],  # new_messages
            MagicMock(),  # chat_context
        )

    # Set up mocks
    create_entries_mock = AsyncMock()

    with (
        patch(
            "agents_api.routers.sessions.legacy.chat.render_chat_input", side_effect=mock_render
        ),
        patch("agents_api.routers.sessions.legacy.chat.create_entries", create_entries_mock),
    ):
        # Create chat input with stream=True and save=True
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
            save=True,
        )

        # Call the chat function with mock response that includes finish_reason
        mock_response = "This is a test response"
        response = await chat(
            developer=developer,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=BackgroundTasks(),
            mock_response=mock_response,
            connection_pool=pool,
        )
        _ = await collect_stream_content(response)

        # Verify create_entries was called for user messages
        create_entries_mock.assert_called_once()
        call_args = create_entries_mock.call_args[1]
        assert call_args["developer_id"] == developer_id
        assert call_args["session_id"] == session.id
        # Verify we're saving the user message
        assert len(call_args["data"]) == 1
        assert call_args["data"][0].role == "user"
        assert call_args["data"][0].content == "Hello"


@test("chat: Test streaming with usage tracking")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that token usage is tracked in streaming responses."""
    pool = await create_db_pool(dsn=dsn)

    # Create a session
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session for streaming usage tracking",
        ),
        connection_pool=pool,
    )

    # Mock render_chat_input to return consistent values
    async def mock_render(*args, **kwargs):
        return (
            [{"role": "user", "content": "Hello"}],  # messages
            [],  # doc_references
            None,  # formatted_tools
            {"model": "gpt-4o-mini"},  # settings
            [{"role": "user", "content": "Hello"}],  # new_messages
            MagicMock(),  # chat_context
        )

    # Mock track_usage to verify it's called
    track_usage_mock = AsyncMock()

    with (
        patch(
            "agents_api.routers.sessions.legacy.chat.render_chat_input", side_effect=mock_render
        ),
        patch("agents_api.routers.sessions.legacy.chat.track_usage", track_usage_mock),
    ):
        # Create chat input with stream=True
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
        )

        # Call the chat function with mock response that includes finish_reason and usage
        mock_response = "This is a test response"
        response = await chat(
            developer=developer,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=BackgroundTasks(),
            mock_response=mock_response,
            connection_pool=pool,
        )

        # Collect and parse stream content
        parsed_chunks = await collect_stream_content(response)

        # Verify usage data in the final chunk
        final_chunk = parsed_chunks[-1]
        assert "usage" in final_chunk
        assert "total_tokens" in final_chunk["usage"]

        # Verify that track_usage was called for database tracking
        track_usage_mock.assert_called_once()
        call_args = track_usage_mock.call_args[1]
        assert call_args["developer_id"] == developer_id
        assert call_args["model"] == "gpt-4o-mini"
        assert call_args["messages"] == [{"role": "user", "content": "Hello"}]
        assert call_args["custom_api_used"] is False
        assert "streaming" in call_args["metadata"]
        assert call_args["metadata"]["streaming"] is True


@test("chat: Test streaming with custom API key")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that streaming works with a custom API key."""
    pool = await create_db_pool(dsn=dsn)

    # Create a session
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session for streaming with custom API key",
        ),
        connection_pool=pool,
    )

    # Mock render_chat_input to return consistent values
    async def mock_render(*args, **kwargs):
        return (
            [{"role": "user", "content": "Hello"}],  # messages
            [],  # doc_references
            None,  # formatted_tools
            {"model": "gpt-4o-mini"},  # settings
            [{"role": "user", "content": "Hello"}],  # new_messages
            MagicMock(),  # chat_context
        )

    with patch(
        "agents_api.routers.sessions.legacy.chat.render_chat_input", side_effect=mock_render
    ):
        # Create chat input with stream=True
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
        )

        # Call the chat function with custom API key and mock response that includes finish_reason
        custom_api_key = "test-api-key"
        mock_response = "This is a test response"
        response = await chat(
            developer=developer,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=BackgroundTasks(),
            x_custom_api_key=custom_api_key,
            mock_response=mock_response,
            connection_pool=pool,
        )

        # Verify response type is StreamingResponse
        assert isinstance(response, StreamingResponse)
        assert response.media_type == "text/event-stream"

        # Collect and parse stream content
        parsed_chunks = await collect_stream_content(response)

        # Verify chunks are received
        assert len(parsed_chunks) > 0


@test("chat: Test streaming creates actual usage records in database")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that streaming creates actual usage records in the database."""
    pool = await create_db_pool(dsn=dsn)

    # Create a session
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session for streaming usage database tracking",
        ),
        connection_pool=pool,
    )

    # Mock render_chat_input to return consistent values
    async def mock_render(*args, **kwargs):
        return (
            [{"role": "user", "content": "Hello"}],  # messages
            [],  # doc_references
            None,  # formatted_tools
            {"model": "gpt-4o-mini"},  # settings
            [{"role": "user", "content": "Hello"}],  # new_messages
            MagicMock(),  # chat_context
        )

    # Get initial usage record count
    initial_records = await get_usage_records(
        dsn=dsn,
        developer_id=str(developer_id),
    )
    initial_count = len(initial_records)

    with patch(
        "agents_api.routers.sessions.legacy.chat.render_chat_input", side_effect=mock_render
    ):
        # Create chat input with stream=True
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
        )

        # Call the chat function with mock response
        mock_response = "This is a test response"
        response = await chat(
            developer=developer,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=BackgroundTasks(),
            mock_response=mock_response,
            connection_pool=pool,
        )

        # Collect and parse stream content to complete the streaming
        parsed_chunks = await collect_stream_content(response)

        # Verify usage data in the final chunk
        final_chunk = parsed_chunks[-1]
        assert "usage" in final_chunk
        assert "total_tokens" in final_chunk["usage"]

    # Get usage records after streaming
    final_records = await get_usage_records(
        dsn=dsn,
        developer_id=str(developer_id),
    )
    final_count = len(final_records)

    await delete_usage_records(dsn=dsn, developer_id=str(developer_id))

    # Verify a new usage record was created
    assert final_count == initial_count + 1

    # Get the latest usage record
    latest_record = final_records[0]  # Records are ordered by created_at DESC

    # Verify the usage record details
    assert str(latest_record["developer_id"]) == str(developer_id)  # UUID comparison
    assert latest_record["model"] == "gpt-4o-mini"
    assert latest_record["prompt_tokens"] > 0
    assert latest_record["completion_tokens"] > 0
    assert float(latest_record["cost"]) > 0  # cost is NUMERIC type
    assert latest_record["custom_api_used"] is False
    assert "streaming" in latest_record["metadata"]
    assert latest_record["metadata"]["streaming"] is True
    assert "tags" in latest_record["metadata"]


@test("chat: Test streaming with custom API key creates correct usage record")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that streaming with custom API key sets custom_api_used correctly."""
    pool = await create_db_pool(dsn=dsn)

    # Create a session
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session for custom API usage tracking",
        ),
        connection_pool=pool,
    )

    # Mock render_chat_input to return consistent values
    async def mock_render(*args, **kwargs):
        return (
            [{"role": "user", "content": "Hello"}],  # messages
            [],  # doc_references
            None,  # formatted_tools
            {"model": "gpt-4o-mini"},  # settings
            [{"role": "user", "content": "Hello"}],  # new_messages
            MagicMock(),  # chat_context
        )

    # Get initial usage record count
    initial_records = await get_usage_records(
        dsn=dsn,
        developer_id=str(developer_id),
    )
    initial_count = len(initial_records)

    with patch(
        "agents_api.routers.sessions.legacy.chat.render_chat_input", side_effect=mock_render
    ):
        # Create chat input with stream=True
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
        )

        # Call the chat function with custom API key
        custom_api_key = "test-custom-api-key"
        mock_response = "This is a test response"
        response = await chat(
            developer=developer,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=BackgroundTasks(),
            x_custom_api_key=custom_api_key,
            mock_response=mock_response,
            connection_pool=pool,
        )

        # Collect and parse stream content to complete the streaming
        parsed_chunks = await collect_stream_content(response)

        # Verify usage data in the final chunk
        final_chunk = parsed_chunks[-1]
        assert "usage" in final_chunk

    # Get usage records after streaming
    final_records = await get_usage_records(
        dsn=dsn,
        developer_id=str(developer_id),
    )
    final_count = len(final_records)

    # Verify a new usage record was created
    assert final_count == initial_count + 1

    # Get the latest usage record
    latest_record = final_records[0]  # Records are ordered by created_at DESC

    # Verify the usage record details for custom API usage
    assert str(latest_record["developer_id"]) == str(developer_id)  # UUID comparison
    assert latest_record["model"] == "gpt-4o-mini"
    assert latest_record["custom_api_used"] is True  # This should be True for custom API
    assert "streaming" in latest_record["metadata"]
    assert latest_record["metadata"]["streaming"] is True


@test("chat: Test streaming usage tracking with developer tags")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that streaming includes developer tags in usage metadata."""
    pool = await create_db_pool(dsn=dsn)

    # Create a session
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session for tags in usage tracking",
        ),
        connection_pool=pool,
    )

    # Mock render_chat_input to return consistent values
    async def mock_render(*args, **kwargs):
        return (
            [{"role": "user", "content": "Hello"}],  # messages
            [],  # doc_references
            None,  # formatted_tools
            {"model": "gpt-4o-mini"},  # settings
            [{"role": "user", "content": "Hello"}],  # new_messages
            MagicMock(),  # chat_context
        )

    # Mock developer with tags
    test_tags = ["tag1", "tag2", "test"]
    developer_with_tags = developer
    developer_with_tags.tags = test_tags

    # Get initial usage record count
    initial_records = await get_usage_records(
        dsn=dsn,
        developer_id=str(developer_id),
    )
    initial_count = len(initial_records)

    with patch(
        "agents_api.routers.sessions.legacy.chat.render_chat_input", side_effect=mock_render
    ):
        # Create chat input with stream=True
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
        )

        # Call the chat function
        mock_response = "This is a test response"
        response = await chat(
            developer=developer_with_tags,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=BackgroundTasks(),
            mock_response=mock_response,
            connection_pool=pool,
        )

        # Collect and parse stream content to complete the streaming
        parsed_chunks = await collect_stream_content(response)

        # Verify usage data in the final chunk
        final_chunk = parsed_chunks[-1]
        assert "usage" in final_chunk

    # Get usage records after streaming
    final_records = await get_usage_records(
        dsn=dsn,
        developer_id=str(developer_id),
    )
    final_count = len(final_records)
    await delete_usage_records(dsn=dsn, developer_id=str(developer_id))

    # Verify a new usage record was created
    assert final_count == initial_count + 1

    # Get the latest usage record
    latest_record = final_records[0]  # Records are ordered by created_at DESC

    # Verify the usage record includes developer tags
    assert str(latest_record["developer_id"]) == str(developer_id)  # UUID comparison
    assert latest_record["model"] == "gpt-4o-mini"
    assert "streaming" in latest_record["metadata"]
    assert latest_record["metadata"]["streaming"] is True
    assert "tags" in latest_record["metadata"]
    assert latest_record["metadata"]["tags"] == test_tags


@test("chat: Test streaming usage tracking with different models")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that streaming correctly tracks usage for different models."""
    pool = await create_db_pool(dsn=dsn)

    # Create a session
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session for different model usage tracking",
        ),
        connection_pool=pool,
    )

    test_model = "gpt-3.5-turbo"

    # Mock render_chat_input to return the test model
    async def mock_render(*args, **kwargs):
        return (
            [{"role": "user", "content": "Hello"}],  # messages
            [],  # doc_references
            None,  # formatted_tools
            {"model": test_model},  # settings
            [{"role": "user", "content": "Hello"}],  # new_messages
            MagicMock(),  # chat_context
        )

    # Get initial usage record count
    initial_records = await get_usage_records(
        dsn=dsn,
        developer_id=str(developer_id),
    )
    initial_count = len(initial_records)

    with patch(
        "agents_api.routers.sessions.legacy.chat.render_chat_input", side_effect=mock_render
    ):
        # Create chat input with stream=True
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
        )

        # Call the chat function
        mock_response = "This is a test response"
        response = await chat(
            developer=developer,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=BackgroundTasks(),
            mock_response=mock_response,
            connection_pool=pool,
        )

        # Collect and parse stream content to complete the streaming
        parsed_chunks = await collect_stream_content(response)

        # Verify usage data in the final chunk
        final_chunk = parsed_chunks[-1]
        assert "usage" in final_chunk

    # Get usage records after streaming
    final_records = await get_usage_records(
        dsn=dsn,
        developer_id=str(developer_id),
    )
    final_count = len(final_records)
    await delete_usage_records(dsn=dsn, developer_id=str(developer_id))

    # Verify a new usage record was created
    assert final_count == initial_count + 1

    # Get the latest usage record
    latest_record = final_records[0]  # Records are ordered by created_at DESC

    # Verify the usage record has the correct model
    assert str(latest_record["developer_id"]) == str(developer_id)  # UUID comparison
    assert latest_record["model"] == test_model
    assert latest_record["prompt_tokens"] > 0
    assert latest_record["completion_tokens"] > 0
    assert float(latest_record["cost"]) > 0  # cost is NUMERIC type
    assert "streaming" in latest_record["metadata"]
    assert latest_record["metadata"]["streaming"] is True

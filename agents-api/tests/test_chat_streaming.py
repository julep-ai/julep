"""Tests for the streaming logic in the chat function."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

from agents_api.autogen.openapi_model import (
    ChatInput,
    CreateSessionRequest,
)
from agents_api.clients.pg import create_db_pool
from agents_api.queries.sessions.create_session import create_session
from agents_api.routers.sessions.chat import chat
from fastapi import BackgroundTasks
from starlette.responses import StreamingResponse
from uuid_extensions import uuid7
from ward import test

from .fixtures import (
    pg_dsn,
    test_agent,
    test_developer,
    test_developer_id,
)


class MockStreamResponse:
    """Mock for a streaming response from litellm."""

    def __init__(self, content: str, n_chunks: int = 3):
        """Create a mock stream response.

        Args:
            content: The content to stream back
            n_chunks: Number of chunks to split the content into
        """
        self.content = content
        self.n_chunks = n_chunks
        self.chunks = []

        # Split content into chunks
        chunk_size = max(1, len(content) // n_chunks)
        for i in range(0, len(content), chunk_size):
            end = min(i + chunk_size, len(content))
            self.chunks.append(content[i:end])

        # Set up usage and choices for model_dump methods
        self.usage = MagicMock()
        self.usage.model_dump.return_value = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        }

        # Current index for iteration
        self._index = 0

    def __aiter__(self):
        """Return self as an async iterator."""
        self._index = 0
        return self

    async def __anext__(self):
        """Get next chunk or raise StopAsyncIteration."""
        if self._index >= len(self.chunks):
            raise StopAsyncIteration

        chunk = self.chunks[self._index]
        self._index += 1

        choice = MagicMock()
        choice.delta.content = chunk
        choice.delta.role = "assistant"
        choice.model_dump.return_value = {
            "index": 0,
            "delta": {"content": chunk, "role": "assistant"},
            "finish_reason": None,
        }

        mock_chunk = MagicMock()
        mock_chunk.choices = [choice]
        return mock_chunk


async def collect_stream_content(response: StreamingResponse) -> str:
    """Helper function to collect and concatenate stream chunks."""
    chunks = []
    async for chunk in response.body_iterator:
        # Ensure we're dealing with string data
        if isinstance(chunk, bytes):
            chunk = chunk.decode("utf-8")
        chunks.append(chunk)

    return "".join(chunks)


def extract_content_from_sse(sse_text: str) -> str:
    """Extract actual content from SSE formatted response.

    Args:
        sse_text: The full SSE formatted response

    Returns:
        Extracted content as a string
    """
    content = ""
    for line in sse_text.split("\n\n"):
        if not line.startswith("data:"):
            continue

        try:
            # Strip "data: " prefix and parse JSON
            data = json.loads(line[6:])

            # Extract content from choices if present
            if "choices" in data:
                for choice in data["choices"]:
                    if "delta" in choice and "content" in choice["delta"]:
                        content += choice["delta"]["content"]
        except (json.JSONDecodeError, KeyError):
            # Skip any lines that don't contain valid JSON or expected structure
            continue

    return content


@test("chat: Test streaming response is returned when stream=True")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that the chat function returns a StreamingResponse when stream=True."""
    pool = await create_db_pool(dsn=dsn)

    # Create a session
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session for streaming",
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

    # Define a mock response
    mock_response = "This is a test streaming response"

    # Mock litellm.acompletion to return our stream response
    mock_stream = MockStreamResponse(mock_response)
    acompletion_mock = AsyncMock(return_value=mock_stream)

    with (
        patch("agents_api.routers.sessions.chat.render_chat_input", side_effect=mock_render),
        patch("agents_api.clients.litellm.acompletion", acompletion_mock),
    ):
        # Create chat input with stream=True
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
        )

        # Call the chat function
        response = await chat(
            developer=developer,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=BackgroundTasks(),
        )

        # Verify response type is StreamingResponse
        assert isinstance(response, StreamingResponse)

        # Test the content of the streaming response
        content_str = await collect_stream_content(response)

        # Verify the response contains expected SSE format and content
        assert "data: " in content_str

        # Check for metadata in the first chunk
        assert '"id":' in content_str
        assert '"created_at":' in content_str

        # Extract the actual content from the SSE response
        extracted_content = extract_content_from_sse(content_str)
        assert mock_response.replace(" ", "") in extracted_content.replace(" ", "")

        # Check for the [DONE] marker at the end
        assert "data: [DONE]" in content_str

        assert response.media_type == "text/event-stream"

        # Verify litellm.acompletion was called with stream=True
        acompletion_mock.assert_called_once()
        assert "stream" in acompletion_mock.call_args[1]
        assert acompletion_mock.call_args[1]["stream"] is True


@test("chat: Test streaming response saves user messages to history when save=True")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that user messages are saved to history when save=True with streaming response."""
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

    # Mock create_entries to verify it's called with correct parameters
    create_entries_mock = AsyncMock()

    # Define a mock response
    mock_response = "This is a test streaming response with history"

    # Mock litellm.acompletion to return our stream response
    mock_stream = MockStreamResponse(mock_response)
    acompletion_mock = AsyncMock(return_value=mock_stream)

    with (
        patch("agents_api.routers.sessions.chat.render_chat_input", side_effect=mock_render),
        patch("agents_api.routers.sessions.chat.create_entries", create_entries_mock),
        patch("agents_api.clients.litellm.acompletion", acompletion_mock),
    ):
        # Create chat input with stream=True and save=True
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
            save=True,
        )

        # Create a BackgroundTasks object with a custom add_task method to capture tasks
        background_tasks = BackgroundTasks()

        # Use a spy to track the add_task method calls
        original_add_task = background_tasks.add_task
        captured_tasks = []

        def add_task_spy(task, *args, **kwargs):
            captured_tasks.append((task, args, kwargs))
            return original_add_task(task, *args, **kwargs)

        background_tasks.add_task = add_task_spy

        # Call the chat function
        response = await chat(
            developer=developer,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=background_tasks,
        )

        # Verify response content
        content_str = await collect_stream_content(response)
        extracted_content = extract_content_from_sse(content_str)
        assert mock_response.replace(" ", "") in extracted_content.replace(" ", "")

        # Verify that background_tasks.add_task was called at least once
        assert len(captured_tasks) >= 1
        task_func, _task_args, task_kwargs = captured_tasks[0]

        # Verify create_entries was added as a background task with correct parameters
        assert task_func == create_entries_mock
        assert task_kwargs["developer_id"] == developer_id
        assert task_kwargs["session_id"] == session.id
        assert len(task_kwargs["data"]) == 1
        assert task_kwargs["data"][0].role == "user"
        assert task_kwargs["data"][0].content == "Hello"
        assert task_kwargs["data"][0].source == "api_request"

        # Verify litellm.acompletion was called with stream=True
        acompletion_mock.assert_called_once()
        assert "stream" in acompletion_mock.call_args[1]
        assert acompletion_mock.call_args[1]["stream"] is True


@test("chat: Test streaming response does not save history when save=False")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that messages are not saved to history when save=False with streaming response."""
    pool = await create_db_pool(dsn=dsn)

    # Create a session
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session for streaming without saving",
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

    # Mock create_entries to verify it's not called
    create_entries_mock = AsyncMock()

    # Define a mock response
    mock_response = "This is a test streaming response without saving"

    # Mock litellm.acompletion to return our stream response
    mock_stream = MockStreamResponse(mock_response)
    acompletion_mock = AsyncMock(return_value=mock_stream)

    with (
        patch("agents_api.routers.sessions.chat.render_chat_input", side_effect=mock_render),
        patch("agents_api.routers.sessions.chat.create_entries", create_entries_mock),
        patch("agents_api.clients.litellm.acompletion", acompletion_mock),
    ):
        # Create chat input with stream=True and save=False
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
            save=False,
        )

        # Create a BackgroundTasks object with a custom add_task method to capture tasks
        background_tasks = BackgroundTasks()

        # Use a spy to track the add_task method calls
        original_add_task = background_tasks.add_task
        captured_tasks = []

        def add_task_spy(task, *args, **kwargs):
            captured_tasks.append((task, args, kwargs))
            return original_add_task(task, *args, **kwargs)

        background_tasks.add_task = add_task_spy

        # Call the chat function
        response = await chat(
            developer=developer,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=background_tasks,
        )

        # Verify response content
        content_str = await collect_stream_content(response)
        extracted_content = extract_content_from_sse(content_str)
        assert mock_response.replace(" ", "") in extracted_content.replace(" ", "")

        # Verify that background_tasks.add_task was not called with create_entries
        assert len(captured_tasks) == 0
        create_entries_mock.assert_not_called()


@test("chat: Test streaming with document references")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that document references are included in streaming response parameters."""
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

    # Create document references
    doc_refs = [
        {"id": str(uuid7()), "title": "Test Document 1"},
        {"id": str(uuid7()), "title": "Test Document 2"},
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

    # Define a mock response
    mock_response = "This is a test streaming response with documents"

    # Mock litellm.acompletion to return our stream response
    mock_stream = MockStreamResponse(mock_response)
    acompletion_mock = AsyncMock(return_value=mock_stream)

    with (
        patch("agents_api.routers.sessions.chat.render_chat_input", side_effect=mock_render),
        patch("agents_api.clients.litellm.acompletion", acompletion_mock),
    ):
        # Create chat input with stream=True
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
        )

        # Call the chat function
        response = await chat(
            developer=developer,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=BackgroundTasks(),
        )

        # Verify content
        content_str = await collect_stream_content(response)
        extracted_content = extract_content_from_sse(content_str)
        assert mock_response.replace(" ", "") in extracted_content.replace(" ", "")

        # Verify that the document references were included in the first data chunk
        # Extract the first data chunk as JSON
        first_chunk = content_str.split("data: ")[1].split("\n\n")[0]
        metadata = json.loads(first_chunk)

        # Check if doc references are included
        assert "docs" in metadata
        assert len(metadata["docs"]) == len(doc_refs)

        # Verify all doc IDs are present
        doc_ids_in_response = [doc["id"] for doc in metadata["docs"]]
        expected_ids = [doc["id"] for doc in doc_refs]
        assert all(doc_id in doc_ids_in_response for doc_id in expected_ids)


@test("chat: Test streaming with custom API key")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that a custom API key is passed correctly with streaming."""
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

    # Define a mock response
    mock_response = "This is a test streaming response with custom API key"

    # Use a real mock instead of a spy - mock the actual response with our MockStreamResponse
    mock_stream = MockStreamResponse(mock_response)
    acompletion_mock = AsyncMock(return_value=mock_stream)

    with (
        patch("agents_api.routers.sessions.chat.render_chat_input", side_effect=mock_render),
        patch("agents_api.clients.litellm.acompletion", acompletion_mock),
    ):
        # Create chat input with stream=True
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
        )

        # Custom API key
        custom_api_key = "sk-test-custom-key"

        # Call the chat function with the custom API key
        response = await chat(
            developer=developer,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=BackgroundTasks(),
            x_custom_api_key=custom_api_key,
        )

        # Verify response content
        content_str = await collect_stream_content(response)
        extracted_content = extract_content_from_sse(content_str)
        assert mock_response.replace(" ", "") in extracted_content.replace(" ", "")

        # Verify litellm.acompletion was called with the custom API key
        acompletion_mock.assert_called_once()
        assert "custom_api_key" in acompletion_mock.call_args[1]
        assert acompletion_mock.call_args[1]["custom_api_key"] == custom_api_key


@test("chat: Test streaming with tools")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test that tools are properly passed when streaming is enabled."""
    pool = await create_db_pool(dsn=dsn)

    # Create a session
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session for streaming with tools",
        ),
        connection_pool=pool,
    )

    # Define sample tools
    formatted_tools = [
        {
            "type": "function",
            "function": {
                "name": "test_tool",
                "description": "A test tool",
                "parameters": {
                    "type": "object",
                    "properties": {"param1": {"type": "string", "description": "A parameter"}},
                    "required": ["param1"],
                },
            },
        }
    ]

    # Mock render_chat_input to return tools
    async def mock_render(*args, **kwargs):
        return (
            [{"role": "user", "content": "Hello"}],  # messages
            [],  # doc_references
            formatted_tools,  # formatted_tools
            {"model": "gpt-4o-mini"},  # settings
            [{"role": "user", "content": "Hello"}],  # new_messages
            MagicMock(),  # chat_context
        )

    # Define a mock response
    mock_response = "This is a test streaming response with tools"

    # Use a real mock instead of a spy - mock the actual response with our MockStreamResponse
    mock_stream = MockStreamResponse(mock_response)
    acompletion_mock = AsyncMock(return_value=mock_stream)

    with (
        patch("agents_api.routers.sessions.chat.render_chat_input", side_effect=mock_render),
        patch("agents_api.clients.litellm.acompletion", acompletion_mock),
    ):
        # Create chat input with stream=True
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
        )

        # Call the chat function
        response = await chat(
            developer=developer,
            session_id=session.id,
            chat_input=chat_input,
            background_tasks=BackgroundTasks(),
        )

        # Verify response content
        content_str = await collect_stream_content(response)
        extracted_content = extract_content_from_sse(content_str)
        assert mock_response.replace(" ", "") in extracted_content.replace(" ", "")

        # Verify litellm.acompletion was called with tools
        acompletion_mock.assert_called_once()
        assert "tools" in acompletion_mock.call_args[1]
        assert acompletion_mock.call_args[1]["tools"] == formatted_tools


@test("chat: Test multiple mock_response formats")
async def _(
    developer=test_developer,
    dsn=pg_dsn,
    developer_id=test_developer_id,
    agent=test_agent,
):
    """Test different formats of mock_response with streaming."""
    pool = await create_db_pool(dsn=dsn)

    # Create a session
    session = await create_session(
        developer_id=developer_id,
        data=CreateSessionRequest(
            agent=agent.id,
            situation="test session for streaming with various mock formats",
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

    with patch("agents_api.routers.sessions.chat.render_chat_input", side_effect=mock_render):
        # 1. Test with string mock_response
        chat_input = ChatInput(
            messages=[{"role": "user", "content": "Hello"}],
            stream=True,
        )

        string_mock = "This is a simple string mock"
        mock_stream = MockStreamResponse(string_mock)
        acompletion_mock = AsyncMock(return_value=mock_stream)

        with patch("agents_api.clients.litellm.acompletion", acompletion_mock):
            response1 = await chat(
                developer=developer,
                session_id=session.id,
                chat_input=chat_input,
                background_tasks=BackgroundTasks(),
            )

            assert isinstance(response1, StreamingResponse)

            # Verify response content
            content_str1 = await collect_stream_content(response1)
            extracted_content1 = extract_content_from_sse(content_str1)
            assert string_mock.replace(" ", "") in extracted_content1.replace(" ", "")
            assert "data: " in content_str1
            assert "data: [DONE]" in content_str1

            # 2. Test with complex JSON-compatible mock_response
            complex_mock = {
                "response": "This is a complex mock",
                "details": {"confidence": 0.95, "source": "test"},
            }

            # We need to convert this to JSON string
            complex_mock_str = json.dumps(complex_mock)
            mock_stream2 = MockStreamResponse(complex_mock_str)
            acompletion_mock2 = AsyncMock(return_value=mock_stream2)

            with patch("agents_api.clients.litellm.acompletion", acompletion_mock2):
                response2 = await chat(
                    developer=developer,
                    session_id=session.id,
                    chat_input=chat_input,
                    background_tasks=BackgroundTasks(),
                )

                assert isinstance(response2, StreamingResponse)

                # Verify response content
                content_str2 = await collect_stream_content(response2)
                extracted_content2 = extract_content_from_sse(content_str2)
                # Check that the JSON content is in the response
                assert "response" in extracted_content2
                assert "complex mock" in extracted_content2
                assert "data: " in content_str2
                assert "data: [DONE]" in content_str2

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from agents_api.routers.utils.tools import (
    _system_tool_handlers,
    call_tool,
    tool_calls_evaluator,
)
from litellm.utils import ModelResponse
from ward import raises, test


@test("call_tool: raises NotImplementedError for unknown tool")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    tool_name = "unknown.tool"
    arguments = {}

    with raises(NotImplementedError) as exc:
        await call_tool(developer_id, tool_name, arguments)

    assert str(exc.raised) == "System call not implemented for unknown.tool"


@test("call_tool: handles agent.doc.list correctly")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    tool_name = "agent.doc.list"
    agent_id = UUID("11111111-1111-1111-1111-111111111111")
    arguments = {"agent_id": agent_id}
    with patch(
        "agents_api.routers.utils.tools.list_docs_query", new_callable=AsyncMock
    ) as mock_list_docs:
        _system_tool_handlers["agent.doc.list"] = mock_list_docs
        mock_list_docs.return_value = ["doc1", "doc2"]
        result = await call_tool(developer_id, tool_name, arguments)

        mock_list_docs.assert_called_once()
        call_args = mock_list_docs.call_args[1]
        assert call_args["developer_id"] == developer_id
        assert call_args["owner_type"] == "agent"
        assert call_args["owner_id"] == agent_id
        assert result == ["doc1", "doc2"]


@test("call_tool: handles agent.doc.create correctly")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    tool_name = "agent.doc.create"
    arguments = {
        "data": {"title": "Test Doc", "content": "Test content"},
        "agent_id": "11111111-1111-1111-1111-111111111111",
    }

    with patch(
        "agents_api.routers.utils.tools.create_agent_doc", new_callable=AsyncMock
    ) as mock_create_doc:
        _system_tool_handlers["agent.doc.create"] = mock_create_doc
        mock_create_doc.return_value = {"id": "doc123", "title": "Test Doc"}
        result = await call_tool(developer_id, tool_name, arguments)

        mock_create_doc.assert_called_once()
        call_args = mock_create_doc.call_args[1]
        assert call_args["x_developer_id"] == developer_id
        assert call_args["agent_id"] == UUID("11111111-1111-1111-1111-111111111111")
        assert result == {"id": "doc123", "title": "Test Doc"}


@test("call_tool: handles agent.doc.delete correctly")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    tool_name = "agent.doc.delete"
    agent_id = UUID("11111111-1111-1111-1111-111111111111")
    doc_id = UUID("22222222-2222-2222-2222-222222222222")
    arguments = {"agent_id": agent_id, "doc_id": doc_id}

    with patch(
        "agents_api.routers.utils.tools.delete_doc_query", new_callable=AsyncMock
    ) as mock_delete_doc:
        _system_tool_handlers["agent.doc.delete"] = mock_delete_doc
        mock_delete_doc.return_value = {"success": True}
        result = await call_tool(developer_id, tool_name, arguments)

        mock_delete_doc.assert_called_once()
        call_args = mock_delete_doc.call_args[1]
        assert call_args["developer_id"] == developer_id
        assert call_args["owner_type"] == "agent"
        assert call_args["owner_id"] == agent_id
        assert call_args["doc_id"] == doc_id
        assert result == {"success": True}


@test("call_tool: handles agent.doc.search correctly")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    tool_name = "agent.doc.search"
    agent_id = UUID("11111111-1111-1111-1111-111111111111")
    arguments = {"agent_id": agent_id, "text": "search query", "limit": 5}

    with patch(
        "agents_api.routers.utils.tools.search_agent_docs", new_callable=AsyncMock
    ) as mock_search_docs:
        _system_tool_handlers["agent.doc.search"] = mock_search_docs
        mock_search_docs.return_value = [
            {"id": "doc1", "score": 0.9},
            {"id": "doc2", "score": 0.8},
        ]
        result = await call_tool(developer_id, tool_name, arguments)

        mock_search_docs.assert_called_once()
        call_args = mock_search_docs.call_args[1]
        assert call_args["x_developer_id"] == developer_id
        assert call_args["agent_id"] == agent_id
        assert "search_params" in call_args
        assert call_args["search_params"].text == "search query"
        assert call_args["search_params"].limit == 5
        assert result == [{"id": "doc1", "score": 0.9}, {"id": "doc2", "score": 0.8}]


@test("call_tool: handles agent.list correctly")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    tool_name = "agent.list"
    arguments = {}

    with patch(
        "agents_api.routers.utils.tools.list_agents_query", new_callable=AsyncMock
    ) as mock_list_agents:
        _system_tool_handlers["agent.list"] = mock_list_agents
        mock_list_agents.return_value = [{"id": "agent1"}, {"id": "agent2"}]
        result = await call_tool(developer_id, tool_name, arguments)

        mock_list_agents.assert_called_once()
        call_args = mock_list_agents.call_args[1]
        assert call_args["developer_id"] == developer_id
        assert result == [{"id": "agent1"}, {"id": "agent2"}]


@test("call_tool: handles agent.get correctly")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    tool_name = "agent.get"
    agent_id = UUID("11111111-1111-1111-1111-111111111111")
    arguments = {"agent_id": agent_id}

    with patch(
        "agents_api.routers.utils.tools.get_agent_query", new_callable=AsyncMock
    ) as mock_get_agent:
        _system_tool_handlers["agent.get"] = mock_get_agent
        mock_get_agent.return_value = {"id": str(agent_id), "name": "Test Agent"}
        result = await call_tool(developer_id, tool_name, arguments)

        mock_get_agent.assert_called_once()
        call_args = mock_get_agent.call_args[1]
        assert call_args["developer_id"] == developer_id
        assert call_args["agent_id"] == agent_id
        assert result == {"id": str(agent_id), "name": "Test Agent"}


@test("call_tool: handles session operations correctly")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    session_id = UUID("33333333-3333-3333-3333-333333333333")

    # Test session.list
    with patch(
        "agents_api.routers.utils.tools.list_sessions_query", new_callable=AsyncMock
    ) as mock_list:
        _system_tool_handlers["session.list"] = mock_list
        mock_list.return_value = [{"id": "session1"}, {"id": "session2"}]
        result = await call_tool(developer_id, "session.list", {})

        mock_list.assert_called_once()
        assert result == [{"id": "session1"}, {"id": "session2"}]

    # Test session.get
    with patch(
        "agents_api.routers.utils.tools.get_session_query", new_callable=AsyncMock
    ) as mock_get:
        _system_tool_handlers["session.get"] = mock_get
        mock_get.return_value = {"id": str(session_id), "name": "Test Session"}
        result = await call_tool(developer_id, "session.get", {"session_id": session_id})

        mock_get.assert_called_once()
        call_args = mock_get.call_args[1]
        assert call_args["session_id"] == session_id
        assert result == {"id": str(session_id), "name": "Test Session"}

    # Test session.history
    with patch(
        "agents_api.routers.utils.tools.get_history_query", new_callable=AsyncMock
    ) as mock_history:
        _system_tool_handlers["session.history"] = mock_history
        mock_history.return_value = [{"message": "Hello"}, {"message": "Hi"}]
        result = await call_tool(developer_id, "session.history", {"session_id": session_id})

        mock_history.assert_called_once()
        call_args = mock_history.call_args[1]
        assert call_args["session_id"] == session_id
        assert result == [{"message": "Hello"}, {"message": "Hi"}]


@test("call_tool: handles task operations correctly")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    task_id = UUID("44444444-4444-4444-4444-444444444444")

    # Test task.list
    with patch(
        "agents_api.routers.utils.tools.list_tasks_query", new_callable=AsyncMock
    ) as mock_list:
        _system_tool_handlers["task.list"] = mock_list
        mock_list.return_value = [{"id": "task1"}, {"id": "task2"}]
        result = await call_tool(developer_id, "task.list", {})

        mock_list.assert_called_once()
        assert result == [{"id": "task1"}, {"id": "task2"}]

    # Test task.get
    with patch(
        "agents_api.routers.utils.tools.get_task_query", new_callable=AsyncMock
    ) as mock_get:
        _system_tool_handlers["task.get"] = mock_get
        mock_get.return_value = {"id": str(task_id), "name": "Test Task"}
        result = await call_tool(developer_id, "task.get", {"task_id": task_id})

        mock_get.assert_called_once()
        call_args = mock_get.call_args[1]
        assert call_args["task_id"] == task_id
        assert result == {"id": str(task_id), "name": "Test Task"}


@test("call_tool: handles user operations correctly")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    user_id = UUID("55555555-5555-5555-5555-555555555555")

    # Test user.list
    with patch(
        "agents_api.routers.utils.tools.list_users_query", new_callable=AsyncMock
    ) as mock_list:
        _system_tool_handlers["user.list"] = mock_list
        mock_list.return_value = [{"id": "user1"}, {"id": "user2"}]
        result = await call_tool(developer_id, "user.list", {})

        mock_list.assert_called_once()
        assert result == [{"id": "user1"}, {"id": "user2"}]

    # Test user.get
    with patch(
        "agents_api.routers.utils.tools.get_user_query", new_callable=AsyncMock
    ) as mock_get:
        _system_tool_handlers["user.get"] = mock_get
        mock_get.return_value = {"id": str(user_id), "name": "Test User"}
        result = await call_tool(developer_id, "user.get", {"user_id": user_id})

        mock_get.assert_called_once()
        call_args = mock_get.call_args[1]
        assert call_args["user_id"] == user_id
        assert result == {"id": str(user_id), "name": "Test User"}


@test("call_tool: handles user.doc operations correctly")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    user_id = UUID("55555555-5555-5555-5555-555555555555")

    # Test user.doc.list
    with patch(
        "agents_api.routers.utils.tools.list_docs_query", new_callable=AsyncMock
    ) as mock_list:
        _system_tool_handlers["user.doc.list"] = mock_list
        mock_list.return_value = [{"id": "doc1"}, {"id": "doc2"}]
        result = await call_tool(developer_id, "user.doc.list", {"user_id": user_id})

        mock_list.assert_called_once()
        call_args = mock_list.call_args[1]
        assert call_args["owner_type"] == "user"
        assert call_args["owner_id"] == user_id
        assert result == [{"id": "doc1"}, {"id": "doc2"}]

    # Test user.doc.search
    with patch(
        "agents_api.routers.utils.tools.search_user_docs", new_callable=AsyncMock
    ) as mock_search:
        _system_tool_handlers["user.doc.search"] = mock_search
        mock_search.return_value = [{"id": "doc1", "score": 0.95}]
        result = await call_tool(
            developer_id, "user.doc.search", {"user_id": user_id, "text": "search query"}
        )

        mock_search.assert_called_once()
        call_args = mock_search.call_args[1]
        assert call_args["user_id"] == user_id
        assert call_args["x_developer_id"] == developer_id
        assert result == [{"id": "doc1", "score": 0.95}]


@test("tool_calls_evaluator: handles tool calls correctly")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    tool_types = {"function"}

    # Create the function mock with string properties, not nested MagicMocks
    function_mock = MagicMock()
    function_mock.name = "agent.get"  # Set as string, not MagicMock
    function_mock.arguments = '{"agent_id": "11111111-1111-1111-1111-111111111111"}'

    # Create the tool call mock
    tool_call_mock = MagicMock()
    tool_call_mock.id = "call1"
    tool_call_mock.type = "function"
    tool_call_mock.function = function_mock

    # Create the message mock with tool calls
    message_mock = MagicMock()
    message_mock.tool_calls = [tool_call_mock]

    # Create the choice mock
    choice_mock = MagicMock()
    choice_mock.message = message_mock

    # Create the final response mock
    mock_response = MagicMock(spec=ModelResponse)
    mock_response.choices = [choice_mock]

    # Second response without tool calls
    second_message = MagicMock()
    second_message.tool_calls = None
    second_choice = MagicMock()
    second_choice.message = second_message
    second_response = MagicMock(spec=ModelResponse)
    second_response.choices = [second_choice]

    # Mock function that returns response with tool calls first time, then without
    mock_func = AsyncMock()
    mock_func.side_effect = [mock_response, second_response]

    # Mock call_tool function
    mock_tool_response = "Tool response"
    with patch(
        "agents_api.routers.utils.tools.call_tool", new_callable=AsyncMock
    ) as mock_call_tool:
        mock_call_tool.return_value = mock_tool_response

        # Apply decorator
        decorated_func = tool_calls_evaluator(tool_types=tool_types, developer_id=developer_id)(
            mock_func
        )

        # Call decorated function
        messages = []
        await decorated_func(messages=messages)

        # Verify call_tool was called with correct args
        mock_call_tool.assert_called_once_with(
            developer_id, "agent.get", {"agent_id": "11111111-1111-1111-1111-111111111111"}
        )

        # Verify messages were updated correctly
        assert len(messages) == 1
        assert messages[0]["tool_call_id"] == "call1"
        assert messages[0]["role"] == "tool"
        assert messages[0]["name"] == "agent.get"
        assert messages[0]["content"] == mock_tool_response


@test("tool_calls_evaluator: skips non-matching tool types")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    tool_types = {"different_type"}

    # Mock response with tool call of wrong type
    mock_response = MagicMock(spec=ModelResponse)
    mock_response.choices = [
        MagicMock(
            message=MagicMock(
                tool_calls=[
                    MagicMock(
                        type="function", function=MagicMock(name="agent.get", arguments="{}")
                    )
                ]
            )
        )
    ]

    mock_func = AsyncMock(return_value=mock_response)

    with patch(
        "agents_api.routers.utils.tools.call_tool", new_callable=AsyncMock
    ) as mock_call_tool:
        decorated_func = tool_calls_evaluator(tool_types=tool_types, developer_id=developer_id)(
            mock_func
        )

        messages = []
        result = await decorated_func(messages=messages)

        # Verify call_tool was not called
        mock_call_tool.assert_not_called()

        # Verify messages were not modified
        assert len(messages) == 0

        # Verify original response was returned
        assert result == mock_response


@test("tool_calls_evaluator: handles responses without choices")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    tool_types = {"function"}

    # Mock response without choices
    mock_response = MagicMock(spec=ModelResponse)
    mock_response.choices = []

    mock_func = AsyncMock(return_value=mock_response)

    with patch(
        "agents_api.routers.utils.tools.call_tool", new_callable=AsyncMock
    ) as mock_call_tool:
        decorated_func = tool_calls_evaluator(tool_types=tool_types, developer_id=developer_id)(
            mock_func
        )

        messages = []
        result = await decorated_func(messages=messages)

        # Verify call_tool was not called
        mock_call_tool.assert_not_called()

        # Verify messages were not modified
        assert len(messages) == 0

        # Verify original response was returned
        assert result == mock_response


@test("tool_calls_evaluator: continues evaluating until no more tool calls")
async def _():
    developer_id = UUID("00000000-0000-0000-0000-000000000000")
    tool_types = {"function"}

    # First tool call - get user
    function_mock1 = MagicMock()
    function_mock1.name = "user.get"
    function_mock1.arguments = '{"user_id": "55555555-5555-5555-5555-555555555555"}'

    tool_call_mock1 = MagicMock()
    tool_call_mock1.id = "call1"
    tool_call_mock1.type = "function"
    tool_call_mock1.function = function_mock1

    # Second tool call - get agent
    function_mock2 = MagicMock()
    function_mock2.name = "agent.get"
    function_mock2.arguments = '{"agent_id": "11111111-1111-1111-1111-111111111111"}'

    tool_call_mock2 = MagicMock()
    tool_call_mock2.id = "call2"
    tool_call_mock2.type = "function"
    tool_call_mock2.function = function_mock2

    # Create three responses in sequence
    first_response = MagicMock(spec=ModelResponse)
    first_response.choices = [MagicMock(message=MagicMock(tool_calls=[tool_call_mock1]))]

    second_response = MagicMock(spec=ModelResponse)
    second_response.choices = [MagicMock(message=MagicMock(tool_calls=[tool_call_mock2]))]

    final_response = MagicMock(spec=ModelResponse)
    final_response.choices = [MagicMock(message=MagicMock(tool_calls=None))]

    # Mock function returns these responses in sequence
    mock_func = AsyncMock()
    mock_func.side_effect = [first_response, second_response, final_response]

    # Mock responses for each tool call
    tool_responses = {
        "user.get": {"id": "user-123", "name": "Test User"},
        "agent.get": {"id": "agent-456", "name": "Test Agent"},
    }

    async def mock_call_tool_side_effect(dev_id, tool_name, arguments):
        return tool_responses[tool_name]

    with patch(
        "agents_api.routers.utils.tools.call_tool", new_callable=AsyncMock
    ) as patched_call_tool:
        patched_call_tool.side_effect = mock_call_tool_side_effect

        # Apply decorator
        decorated_func = tool_calls_evaluator(tool_types=tool_types, developer_id=developer_id)(
            mock_func
        )

        # Call decorated function
        messages = []
        result = await decorated_func(messages=messages)

        # Verify we got the final response
        assert result == final_response

        # Verify the original function was called 3 times
        assert mock_func.call_count == 3

        # Verify call_tool was called for both tools
        assert patched_call_tool.call_count == 2

        # Verify calls were made with correct arguments
        calls = patched_call_tool.call_args_list
        assert calls[0][0][1] == "user.get"  # First call, tool name
        assert calls[1][0][1] == "agent.get"  # Second call, tool name

        # Verify messages have both tool responses in the right order
        assert len(messages) == 2
        assert messages[0]["tool_call_id"] == "call1"
        assert messages[0]["name"] == "user.get"
        assert messages[0]["content"] == tool_responses["user.get"]

        assert messages[1]["tool_call_id"] == "call2"
        assert messages[1]["name"] == "agent.get"
        assert messages[1]["content"] == tool_responses["agent.get"]

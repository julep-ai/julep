"""Tests for list_secrets_query usage in render.py and tasks.py."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from agents_api.autogen.Agents import Agent
from agents_api.autogen.openapi_model import (
    ChatInput,
    TaskSpecDef,
    TransitionTarget,
    Workflow,
)
from agents_api.autogen.openapi_model import TaskToolDef, Secret, PromptItem, PromptStep, Tool
from agents_api.common.protocol.models import ExecutionInput
from agents_api.common.protocol.tasks import StepContext
from agents_api.common.utils.datetime import utcnow
from agents_api.routers.sessions.render import render_chat_input
from ward import test, skip

from tests.fixtures import test_developer, test_developer_id

@skip("Skipping secrets usage tests")
@test("render: list_secrets_query usage in render_chat_input")
async def _(developer=test_developer):
    # Create test secrets
    test_secrets = [
        Secret(
            id=uuid4(),
            name="api_key",
            value="sk_test_123456789",
            developer_id=developer.id,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        ),
        Secret(
            id=uuid4(),
            name="service_token",
            value="token_987654321",
            developer_id=developer.id,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        ),
    ]

    # Create tools that use secret expressions
    tools = [
        Tool(
            id=uuid4(),
            name="api_tool",
            type="computer_20241022",
            computer_20241022={
                "path": "/usr/bin/curl",
                "api_key": "$ secrets.api_key",
                "auth_token": "$ secrets.service_token",
            },
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        )
    ]

    # Create mock chat context
    mock_chat_context = MagicMock()
    mock_chat_context.session.render_templates = True
    mock_chat_context.session.context_overflow = "error"
    mock_chat_context.get_active_tools.return_value = tools
    mock_chat_context.settings = {"model": "claude-3.5-sonnet"}
    mock_chat_context.get_chat_environment.return_value = {}
    mock_chat_context.merge_system_template.return_value = "System: Use tools to help the user"

    # Mock input data
    session_id = uuid4()
    chat_input = ChatInput(messages=[{"role": "user", "content": "hi"}])

    # Set up mocking for required functions
    with (
        patch(
            "agents_api.routers.sessions.render.list_secrets_query"
        ) as mock_list_secrets_query,
        patch(
            "agents_api.routers.sessions.render.prepare_chat_context"
        ) as mock_prepare_chat_context,
        patch("agents_api.routers.sessions.render.gather_messages") as mock_gather_messages,
        patch("agents_api.routers.sessions.render.render_template") as mock_render_template,
        patch(
            "agents_api.routers.sessions.render.evaluate_expressions"
        ) as mock_render_evaluate_expressions,
        patch("agents_api.routers.sessions.render.validate_model") as mock_validate_model,
    ):
        # Set up return values for mocks
        mock_validate_model.return_value = None
        mock_list_secrets_query.return_value = test_secrets
        mock_prepare_chat_context.return_value = mock_chat_context
        mock_gather_messages.return_value = ([], [])
        mock_render_template.return_value = [
            {"role": "system", "content": "System: Use tools to help the user"}
        ]

        # Set up evaluate_expressions to properly substitute secrets
        def evaluate_side_effect(value, values):
            if isinstance(value, str) and "$ secrets." in value:
                if "$secrets.api_key" in value:
                    return value.replace("$ secrets.api_key", "sk_test_123456789")
                if "$secrets.service_token" in value:
                    return value.replace("$ secrets.service_token", "token_987654321")
            return value

        mock_render_evaluate_expressions.side_effect = evaluate_side_effect

        # Call the function being tested
        _messages, _doc_refs, formatted_tools, *_ = await render_chat_input(
            developer=developer,
            session_id=session_id,
            chat_input=chat_input,
        )

        # Assert that list_secrets_query was called with the right parameters
        mock_list_secrets_query.assert_called_once_with(developer_id=developer.id)

        # Verify that expressions were evaluated
        mock_render_evaluate_expressions.assert_called()

        # Check that formatted_tools contains the evaluated secrets
        assert formatted_tools is not None
        assert len(formatted_tools) > 0

        # The first tool should be the computer_20241022 tool
        tool = formatted_tools[0]
        assert tool["type"] == "computer_20241022"

        # Verify that the secrets were evaluated in the function parameters
        function_params = tool["function"]["parameters"]
        assert "api_key" in function_params, print(tool)
        assert function_params["api_key"] == "sk_test_123456789"
        assert "auth_token" in function_params
        assert function_params["auth_token"] == "token_987654321"


@skip("Skipping secrets usage tests")
@test("tasks: list_secrets_query with multiple secrets")
async def _(developer_id=test_developer_id):
    # Create test secrets with varying names
    test_secrets = [
        Secret(
            id=uuid4(),
            name="api_key_1",
            value="sk_test_123",
            developer_id=developer_id,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        ),
        Secret(
            id=uuid4(),
            name="api_key_2",
            value="sk_test_456",
            developer_id=developer_id,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        ),
        Secret(
            id=uuid4(),
            name="database_url",
            value="postgresql://user:password@localhost:5432/db",
            developer_id=developer_id,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        ),
    ]

    # Create tools that use secret expressions
    task_tools = [
        TaskToolDef(
            type="function",
            name="multi_secret_tool",
            spec={
                "primary_key": "$secrets.api_key_1",
                "secondary_key": "$secrets.api_key_2",
                "connection_string": "$secrets.database_url",
                "url": "https://api.example.com",
            },
        ),
        TaskToolDef(
            type="api_call",
            name="second_tool",
            spec={
                "headers": {"Authorization": "Bearer $secrets.api_key_1"},
                "url": "https://api.example.com/v2",
            },
        ),
    ]

    # Create a valid prompt step for the workflow
    test_prompt_step = PromptStep(
        kind_="prompt",
        prompt=[PromptItem(role="user", content="Test prompt content")],
    )

    # Create a mock workflow with a proper step
    test_workflow = Workflow(name="main", steps=[test_prompt_step])

    # Create a proper TaskSpecDef
    task_spec = TaskSpecDef(
        id=uuid4(),
        name="test_task",
        created_at=utcnow(),
        updated_at=utcnow(),
        workflows=[test_workflow],
        tools=task_tools,
        inherit_tools=False,
    )

    # Create a proper Agent
    test_agent = Agent(
        id=uuid4(), name="test_agent", model="gpt-4", created_at=utcnow(), updated_at=utcnow()
    )

    # Create execution input with the task
    execution_input = ExecutionInput(
        developer_id=developer_id,
        agent=test_agent,
        agent_tools=[],
        arguments={},
        task=task_spec,
    )

    # Create a transition target pointing to the workflow step
    cursor = TransitionTarget(workflow="main", step=0, scope_id=uuid4())

    # Set up the step context properly
    step_context = StepContext(
        loaded=True, execution_input=execution_input, cursor=cursor, current_input={}
    )

    # Mock the current step to use all tools
    with (
        patch("agents_api.common.protocol.tasks.list_secrets_query") as mock_list_secrets_query,
        patch(
            "agents_api.common.protocol.tasks.evaluate_expressions"
        ) as mock_evaluate_expressions,
    ):
        # Set mock return values
        mock_list_secrets_query.return_value = test_secrets
        # Have evaluate_expressions pass through the values but replace secret expressions
        mock_evaluate_expressions.side_effect = lambda spec, values: {
            k: v.replace("$secrets.api_key_1", "sk_test_123")
            .replace("$secrets.api_key_2", "sk_test_456")
            .replace("$secrets.database_url", "postgresql://user:password@localhost:5432/db")
            if isinstance(v, str)
            else v
            for k, v in spec.items()
        }

        # Call the tools method
        tools = await step_context.tools()

        # Assert that list_secrets_query was called with the right parameters
        mock_list_secrets_query.assert_called_once_with(developer_id=developer_id)

        # Verify the right number of tools were created
        assert len(tools) == len(task_tools)

        # Verify evaluate_expressions was called for each tool
        assert mock_evaluate_expressions.call_count == len(task_tools)


@skip("Skipping secrets usage tests")
@test("tasks: list_secrets_query in StepContext.tools method")
async def _(developer_id=test_developer_id):
    # Create test secrets
    test_secrets = [
        Secret(
            id=uuid4(),
            name="api_key",
            value="sk_test_123456789",
            developer_id=developer_id,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        ),
        Secret(
            id=uuid4(),
            name="access_token",
            value="at_test_987654321",
            developer_id=developer_id,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z",
        ),
    ]

    # Create tools that use secret expressions
    task_tools = [
        TaskToolDef(
            type="function",
            name="test_tool_with_secret",
            spec={"api_key": "$secrets.api_key", "url": "https://api.example.com"},
        )
    ]

    # Create a valid prompt step for the workflow
    test_prompt_step = PromptStep(
        kind_="prompt",
        prompt=[PromptItem(role="user", content="Test prompt content")],
    )

    # Create a mock workflow with a proper step
    test_workflow = Workflow(name="main", steps=[test_prompt_step])

    # Create a proper TaskSpecDef
    task_spec = TaskSpecDef(
        id=uuid4(),
        name="test_task",
        created_at=utcnow(),
        updated_at=utcnow(),
        workflows=[test_workflow],
        tools=task_tools,
        inherit_tools=False,
    )

    # Create a proper Agent
    test_agent = Agent(
        id=uuid4(), name="test_agent", model="gpt-4", created_at=utcnow(), updated_at=utcnow()
    )

    # Create execution input with the task
    execution_input = ExecutionInput(
        developer_id=developer_id,
        agent=test_agent,
        agent_tools=[],
        arguments={},
        task=task_spec,
    )

    # Create a transition target pointing to the workflow step
    cursor = TransitionTarget(workflow="main", step=0, scope_id=uuid4())

    # Set up the step context properly
    step_context = StepContext(
        loaded=True, execution_input=execution_input, cursor=cursor, current_input={}
    )

    # Mock the current step to use all tools
    with (
        patch.object(step_context, "current_step", MagicMock(tools="all")),
        patch("agents_api.common.protocol.tasks.list_secrets_query") as mock_list_secrets_query,
    ):
        # Set mock return value
        mock_list_secrets_query.return_value = test_secrets

        # Call the tools method
        tools = await step_context.tools()

        # Assert that list_secrets_query was called with the right parameters
        mock_list_secrets_query.assert_called_once_with(developer_id=developer_id)

        # Verify tools were created with evaluated secrets
        assert len(tools) == len(task_tools)

        # StepContext.tools() returns the correct tools
        assert len(tools) > 0

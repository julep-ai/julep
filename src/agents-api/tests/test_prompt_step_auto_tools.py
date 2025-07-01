from unittest.mock import AsyncMock, patch
from uuid import uuid4

from agents_api.activities.task_steps.prompt_step import prompt_step
from agents_api.autogen.openapi_model import (
    Agent,
    CreateToolRequest,
    FunctionDef,
    PromptStep,
    TaskSpecDef,
    TransitionTarget,
    Workflow,
)
from agents_api.common.protocol.tasks import ExecutionInput, StepContext
from agents_api.common.utils.datetime import utcnow
from ward import test


@test("prompt_step uses auto tool calls when feature flag is enabled")
async def _():
    tool = CreateToolRequest(
        name="test_tool",
        type="function",
        function=FunctionDef(
            parameters={"type": "object", "properties": {"param": {"type": "string"}}},
        ),
        description="Test function",
    )

    # Mock feature flag to be enabled
    with patch("agents_api.activities.task_steps.prompt_step.get_feature_flag_value") as mock_flag:
        mock_flag.return_value = True

        # Mock base_evaluate to just return the prompt unchanged
        with patch("agents_api.activities.task_steps.prompt_step.base_evaluate") as mock_eval:
            mock_eval.return_value = "Test prompt"

            # Mock run_llm_with_tools
            with patch(
                "agents_api.activities.task_steps.prompt_step.run_llm_with_tools",
                new_callable=AsyncMock,
            ) as mock_run_llm:
                mock_run_llm.return_value = [
                    {"role": "user", "content": "Test prompt"},
                    {"role": "assistant", "content": "Test response"},
                ]

                # Create proper StepContext with real objects
                step = PromptStep(prompt="Test prompt", unwrap=False)
                execution_input = ExecutionInput(
                    developer_id=uuid4(),
                    agent=Agent(
                        id=uuid4(),
                        name="test_agent",
                        model="gpt-4",
                        default_settings={"temperature": 0.7},
                        created_at=utcnow(),
                        updated_at=utcnow(),
                    ),
                    agent_tools=[],
                    arguments={},
                    task=TaskSpecDef(
                        name="test_task",
                        tools=[],
                        workflows=[Workflow(name="main", steps=[step])],
                    ),
                )
                
                context = StepContext(
                    execution_input=execution_input,
                    current_input="test input",
                    cursor=TransitionTarget(
                        workflow="main",
                        step=0,
                        scope_id=uuid4(),
                    ),
                )

                # Mock the tools method on the StepContext class - need to accept self parameter
                async def mock_tools_method(self):
                    return [tool]

                with patch.object(StepContext, 'tools', mock_tools_method):
                    # Run the activity
                    result = await prompt_step(context)

                    # Verify run_llm_with_tools was called
                    mock_run_llm.assert_called_once()
                    call_args = mock_run_llm.call_args
                    assert call_args[1]["messages"] == [{"role": "user", "content": "Test prompt"}]
                    assert len(call_args[1]["tools"]) == 1
                    assert call_args[1]["tools"][0].name == "test_tool"

                    # Check result
                    assert result.output == [
                        {"role": "user", "content": "Test prompt"},
                        {"role": "assistant", "content": "Test response"},
                    ]


@test("prompt_step with auto tools handles unwrap correctly")
async def _():
    # Mock feature flag to be enabled
    with patch("agents_api.activities.task_steps.prompt_step.get_feature_flag_value") as mock_flag:
        mock_flag.return_value = True

        # Mock base_evaluate
        with patch("agents_api.activities.task_steps.prompt_step.base_evaluate") as mock_eval:
            mock_eval.return_value = "Test prompt"

            # Mock run_llm_with_tools to return unwrappable response
            with patch(
                "agents_api.activities.task_steps.prompt_step.run_llm_with_tools",
                new_callable=AsyncMock,
            ) as mock_run_llm:
                mock_run_llm.return_value = [
                    {"role": "user", "content": "Test prompt"},
                    {"role": "assistant", "content": "Unwrapped response", "tool_calls": None},
                ]

                # Create proper StepContext with real objects
                step = PromptStep(prompt="Test prompt", unwrap=True)
                execution_input = ExecutionInput(
                    developer_id=uuid4(),
                    agent=Agent(
                        id=uuid4(),
                        name="test_agent",
                        model="gpt-4",
                        default_settings={},
                        created_at=utcnow(),
                        updated_at=utcnow(),
                    ),
                    agent_tools=[],
                    arguments={},
                    task=TaskSpecDef(
                        name="test_task",
                        tools=[],
                        workflows=[Workflow(name="main", steps=[step])],
                    ),
                )
                
                context = StepContext(
                    execution_input=execution_input,
                    current_input="test input",
                    cursor=TransitionTarget(
                        workflow="main",
                        step=0,
                        scope_id=uuid4(),
                    ),
                )

                # Mock the tools method on the StepContext class - need to accept self parameter
                async def mock_tools_method(self):
                    return []

                with patch.object(StepContext, 'tools', mock_tools_method):
                    # Run the activity
                    result = await prompt_step(context)

                    # Check that output is unwrapped
                    assert result.output == "Unwrapped response"
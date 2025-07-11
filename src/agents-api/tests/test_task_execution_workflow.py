import uuid
from base64 import b64decode
from datetime import timedelta
from unittest.mock import Mock, call, patch

import aiohttp
from agents_api.activities import task_steps
from agents_api.activities.execute_api_call import execute_api_call
from agents_api.activities.execute_integration import execute_integration
from agents_api.activities.execute_system import execute_system
from agents_api.activities.task_steps.base_evaluate import base_evaluate
from agents_api.autogen.openapi_model import (
    Agent,
    ApiCallDef,
    BaseIntegrationDef,
    CaseThen,
    EvaluateStep,
    Execution,
    ForeachDo,
    ForeachStep,
    GetStep,
    IfElseWorkflowStep,
    LogStep,
    MapReduceStep,
    PromptItem,
    PromptStep,
    ReturnStep,
    SetStep,
    SwitchStep,
    SystemDef,
    TaskSpecDef,
    TaskToolDef,
    ToolCallStep,
    Transition,
    TransitionTarget,
    WaitForInputInfo,
    WaitForInputStep,
    Workflow,
    YieldStep,
)
from agents_api.common.protocol.tasks import (
    ExecutionInput,
    PartialTransition,
    StepContext,
    StepOutcome,
    WorkflowResult,
)
from agents_api.common.retry_policies import DEFAULT_RETRY_POLICY
from agents_api.common.utils.datetime import utcnow
from agents_api.env import (
    debug,
    temporal_heartbeat_timeout,
    temporal_schedule_to_close_timeout,
    testing,
)
from agents_api.workflows.task_execution import TaskExecutionWorkflow
from aiohttp import test_utils
from temporalio.exceptions import ApplicationError
from temporalio.workflow import _NotInWorkflowEventLoopError
from ward import raises, test


@test("task execution workflow: handle function tool call step")
async def _():
    async def _resp():
        return "function_tool_call_response"

    wf = TaskExecutionWorkflow()
    step = ToolCallStep(tool="tool1")
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=uuid.uuid4(),
        ),
    )
    output = {"type": "function"}
    outcome = StepOutcome(output=output)
    with patch("agents_api.workflows.task_execution.workflow") as workflow:
        workflow.execute_activity.return_value = _resp()
        wf.context = context
        wf.outcome = outcome
        result = await wf.handle_step(
            step=step,
        )
        assert result == WorkflowResult(
            state=PartialTransition(type="resume", output="function_tool_call_response"),
        )
        workflow.execute_activity.assert_called_once_with(
            task_steps.raise_complete_async,
            args=[context, output],
            schedule_to_close_timeout=timedelta(days=31),
            retry_policy=DEFAULT_RETRY_POLICY,
            heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
        )


@test("task execution workflow: handle integration tool call step")
async def _():
    async def _resp():
        return "integration_tool_call_response"

    wf = TaskExecutionWorkflow()
    step = ToolCallStep(tool="tool1")
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[TaskToolDef(type="integration", name="tool1", spec={})],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=uuid.uuid4(),
        ),
    )
    tool_name = "tool1"
    arguments = {}
    outcome = StepOutcome(
        output={
            "type": "integration",
            "integration": {"name": tool_name, "arguments": arguments},
        },
    )

    with (
        patch("agents_api.workflows.task_execution.workflow") as workflow,
        patch("agents_api.common.protocol.tasks.workflow") as context_workflow,
        patch("agents_api.common.protocol.tasks.list_secrets_query") as mock_list_secrets,
    ):
        # Set up the mock to raise the expected exception
        context_workflow.execute_activity.side_effect = _NotInWorkflowEventLoopError(
            "Not in workflow event loop"
        )
        mock_list_secrets.return_value = []

        # Set up the activity execution mock
        workflow.execute_activity.return_value = _resp()
        wf.context = context
        wf.outcome = outcome
        result = await wf.handle_step(
            step=step,
        )
        assert result == WorkflowResult(
            state=PartialTransition(output="integration_tool_call_response"),
        )
        provider = "dummy"
        method = None
        integration = BaseIntegrationDef(
            provider=provider,
            setup=None,
            method=method,
            arguments=arguments,
        )
        workflow.execute_activity.assert_called_once_with(
            execute_integration,
            args=[
                execution_input.developer_id,
                execution_input.agent.id,
                execution_input.task.id if execution_input.task else None,
                None,  # session_id is None for task execution
                tool_name,
                integration,
                arguments,
            ],
            schedule_to_close_timeout=timedelta(
                seconds=30 if debug or testing else temporal_schedule_to_close_timeout,
            ),
            retry_policy=DEFAULT_RETRY_POLICY,
            heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
        )


@test("task execution workflow: handle integration tool call step, integration tools not found")
async def _():
    wf = TaskExecutionWorkflow()
    step = ToolCallStep(tool="tool1")
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[TaskToolDef(type="integration", name="tool2", spec={})],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=uuid.uuid4(),
        ),
    )
    outcome = StepOutcome(
        output={"type": "integration", "integration": {"name": "tool1", "arguments": {}}},
    )
    with (
        patch("agents_api.workflows.task_execution.workflow") as workflow,
        patch("agents_api.common.protocol.tasks.workflow") as context_workflow,
        patch("agents_api.common.protocol.tasks.list_secrets_query") as mock_list_secrets,
    ):
        # Set up the mock to raise the expected exception
        context_workflow.execute_activity.side_effect = _NotInWorkflowEventLoopError(
            "Not in workflow event loop"
        )
        mock_list_secrets.return_value = []
        workflow.execute_activity.return_value = "integration_tool_call_response"
        with raises(ApplicationError) as exc:
            wf.context = context
            wf.outcome = outcome
            await wf.handle_step(
                step=step,
            )
        assert str(exc.raised) == "Integration tool1 not found"


@test("task execution workflow: handle api_call tool call step")
async def _():
    async def _resp():
        return "api_call_tool_call_response"

    wf = TaskExecutionWorkflow()
    arguments = {
        "method": "GET",
        "url": "http://url1.com",
    }
    step = ToolCallStep(
        tool="tool1",
        arguments=arguments,
    )
    execution_input = ExecutionInput(
        arguments=arguments,
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        task=TaskSpecDef(
            name="task1",
            tools=[
                TaskToolDef(
                    type="api_call",
                    name="tool1",
                    spec=arguments,
                    inherited=False,
                ),
            ],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=uuid.uuid4(),
        ),
    )
    outcome = StepOutcome(
        output={
            "type": "api_call",
            "api_call": {
                "arguments": arguments,
                "name": "tool1",
            },
        },
    )
    with (
        patch("agents_api.workflows.task_execution.workflow") as workflow,
        patch("agents_api.common.protocol.tasks.workflow") as context_workflow,
        patch("agents_api.common.protocol.tasks.list_secrets_query") as mock_list_secrets,
    ):
        # Set up the mock to raise the expected exception
        context_workflow.execute_activity.side_effect = _NotInWorkflowEventLoopError(
            "Not in workflow event loop"
        )
        mock_list_secrets.return_value = []
        workflow.execute_activity.return_value = _resp()
        wf.context = context
        wf.outcome = outcome
        result = await wf.handle_step(
            step=step,
        )
        assert result == WorkflowResult(
            state=PartialTransition(output="api_call_tool_call_response"),
        )
        api_call = ApiCallDef(
            method="GET",
            url="http://url1.com",
            headers=None,
            follow_redirects=None,
        )
        workflow.execute_activity.assert_called_once_with(
            execute_api_call,
            args=[
                api_call,
                arguments,
            ],
            schedule_to_close_timeout=timedelta(
                seconds=30 if debug or testing else temporal_schedule_to_close_timeout,
            ),
            heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
        )


@test("task execution workflow: handle api_call tool call step with Method Override")
async def _():
    async def _resp():
        return "api_call_tool_call_response"

    wf = TaskExecutionWorkflow()
    arguments = {
        "method": "POST",
        "url": "http://url1.com",
    }
    input_arguments = {
        "method": "GET",
        "url": "http://url1.com",
    }
    step = ToolCallStep(
        tool="tool1",
        arguments=input_arguments,
    )
    execution_input = ExecutionInput(
        arguments=input_arguments,
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        task=TaskSpecDef(
            name="task1",
            tools=[
                TaskToolDef(
                    type="api_call",
                    name="tool1",
                    spec=arguments,
                    inherited=False,
                ),
            ],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=uuid.uuid4(),
        ),
    )
    outcome = StepOutcome(
        output={
            "type": "api_call",
            "api_call": {
                "arguments": input_arguments,
                "name": "tool1",
            },
        },
    )
    with (
        patch("agents_api.workflows.task_execution.workflow") as workflow,
        patch("agents_api.common.protocol.tasks.workflow") as context_workflow,
        patch("agents_api.common.protocol.tasks.list_secrets_query") as mock_list_secrets,
    ):
        # Set up the mock to raise the expected exception
        context_workflow.execute_activity.side_effect = _NotInWorkflowEventLoopError(
            "Not in workflow event loop"
        )
        mock_list_secrets.return_value = []

        workflow.execute_activity.return_value = _resp()
        wf.context = context
        wf.outcome = outcome
        result = await wf.handle_step(
            step=step,
        )
        assert result == WorkflowResult(
            state=PartialTransition(output="api_call_tool_call_response"),
        )
        api_call = ApiCallDef(
            method="POST",
            url="http://url1.com",
            headers=None,
            follow_redirects=None,
        )
        workflow.execute_activity.assert_called_once_with(
            execute_api_call,
            args=[
                api_call,
                input_arguments,
            ],
            schedule_to_close_timeout=timedelta(
                seconds=30 if debug or testing else temporal_schedule_to_close_timeout,
            ),
            heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
        )


@test(
    "task execution workflow: handle api call tool call step, do not include response content"
)
async def _():
    # Create application with route
    app = aiohttp.web.Application()

    async def handler(request):
        return aiohttp.web.json_response({"test": "data"})

    app.router.add_post("/", handler)

    # Set up mock HTTP server with the pre-configured app
    async with test_utils.TestServer(app) as server:
        # Use the actual server URL
        server_url = str(server.make_url("/"))

        input_arguments = {
            "method": "POST",
            "url": server_url,
            "include_response_content": False,
        }
        api_call = ApiCallDef(
            method="POST",
            url=server_url,
            headers=None,
            follow_redirects=None,
            include_response_content=False,
        )

        result = await execute_api_call(api_call, input_arguments)
        assert "content" not in result
        assert result["status_code"] == 200


@test("task execution workflow: handle api call tool call step, include response content")
async def _():
    # Create application with route
    app = aiohttp.web.Application()

    async def handler(request):
        return aiohttp.web.json_response({"test": "data"})

    app.router.add_post("/", handler)

    # Set up mock HTTP server with the pre-configured app
    async with test_utils.TestServer(app) as server:
        # Use the actual server URL
        server_url = str(server.make_url("/"))

        input_arguments = {
            "method": "POST",
            "url": server_url,
            "include_response_content": True,
        }
        api_call = ApiCallDef(
            method="POST",
            url=server_url,
            headers=None,
            follow_redirects=None,
            include_response_content=False,
        )

        result = await execute_api_call(api_call, input_arguments)
        assert "content" in result
        assert b64decode(result["content"]).decode("utf-8") == '{"test": "data"}'
        assert result["status_code"] == 200

    async with test_utils.TestServer(app) as server:
        # Use the actual server URL
        server_url = str(server.make_url("/"))

        input_arguments = {
            "method": "POST",
            "url": server_url,
            "include_response_content": False,
        }
        api_call = ApiCallDef(
            method="POST",
            url=server_url,
            headers=None,
            follow_redirects=None,
            include_response_content=True,
        )

        result = await execute_api_call(api_call, input_arguments)
        assert "content" in result
        assert b64decode(result["content"]).decode("utf-8") == '{"test": "data"}'
        assert result["status_code"] == 200

    async with test_utils.TestServer(app) as server:
        # Use the actual server URL
        server_url = str(server.make_url("/"))

        input_arguments = {
            "method": "POST",
            "url": server_url,
            "include_response_content": None,
        }
        api_call = ApiCallDef(
            method="POST",
            url=server_url,
            headers=None,
            follow_redirects=None,
            include_response_content=True,
        )

        result = await execute_api_call(api_call, input_arguments)
        assert "content" in result
        assert b64decode(result["content"]).decode("utf-8") == '{"test": "data"}'
        assert result["status_code"] == 200

    async with test_utils.TestServer(app) as server:
        # Use the actual server URL
        server_url = str(server.make_url("/"))

        input_arguments = {
            "method": "POST",
            "url": server_url,
            "include_response_content": True,
        }
        api_call = ApiCallDef(
            method="POST",
            url=server_url,
            headers=None,
            follow_redirects=None,
            include_response_content=True,
        )

        result = await execute_api_call(api_call, input_arguments)
        assert "content" in result
        assert b64decode(result["content"]).decode("utf-8") == '{"test": "data"}'
        assert result["status_code"] == 200


@test("task execution workflow: handle system tool call step")
async def _():
    async def _resp():
        return "system_tool_call_response"

    wf = TaskExecutionWorkflow()
    arguments = {
        "resource": "agent",
        "operation": "create",
        "subresource": "doc",
    }
    step = ToolCallStep(
        tool="tool1",
        arguments=arguments,
    )
    execution_input = ExecutionInput(
        arguments=arguments,
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        task=TaskSpecDef(
            name="task1",
            tools=[
                TaskToolDef(
                    type="system",
                    name="tool1",
                    spec=arguments,
                    inherited=False,
                ),
            ],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=uuid.uuid4(),
        ),
    )
    outcome = StepOutcome(
        output={
            "type": "system",
            "system": {
                **arguments,
                "name": "tool1",
            },
        },
    )
    with patch("agents_api.workflows.task_execution.workflow") as workflow:
        workflow.execute_activity.return_value = _resp()
        wf.context = context
        wf.outcome = outcome
        result = await wf.handle_step(
            step=step,
        )
        assert result == WorkflowResult(
            state=PartialTransition(output="system_tool_call_response"),
        )
        system_call = SystemDef(
            resource="agent",
            operation="create",
            subresource="doc",
        )
        workflow.execute_activity.assert_called_once_with(
            execute_system,
            args=[execution_input.developer_id, system_call],
            schedule_to_close_timeout=timedelta(
                seconds=30 if debug or testing else temporal_schedule_to_close_timeout,
            ),
            heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
        )


@test("task execution workflow: handle switch step, index is positive")
async def _():
    wf = TaskExecutionWorkflow()
    step = SwitchStep(switch=[CaseThen(case="_", then=GetStep(get="key1"))])
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=uuid.uuid4(),
        ),
    )
    outcome = StepOutcome(output=1)
    with patch(
        "agents_api.workflows.task_execution.execute_switch_branch",
    ) as execute_switch_branch:
        execute_switch_branch.return_value = WorkflowResult(
            state=PartialTransition(output="switch_response"),
        )
        wf.context = context
        wf.outcome = outcome
        result = await wf.handle_step(
            step=step,
        )
        assert result == WorkflowResult(state=PartialTransition(output="switch_response"))


@test("task execution workflow: handle switch step, index is negative")
async def _():
    wf = TaskExecutionWorkflow()
    step = SwitchStep(switch=[CaseThen(case="_", then=GetStep(get="key1"))])
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=uuid.uuid4(),
        ),
    )
    outcome = StepOutcome(output=-1)
    with patch("agents_api.workflows.task_execution.workflow") as workflow:
        workflow.logger = Mock()
        with raises(ApplicationError):
            wf.context = context
            wf.outcome = outcome
            await wf.handle_step(
                step=step,
            )


@test("task execution workflow: handle switch step, index is zero")
async def _():
    wf = TaskExecutionWorkflow()
    step = SwitchStep(switch=[CaseThen(case="_", then=GetStep(get="key1"))])
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=uuid.uuid4(),
        ),
    )
    outcome = StepOutcome(output=0)
    with patch(
        "agents_api.workflows.task_execution.execute_switch_branch",
    ) as execute_switch_branch:
        execute_switch_branch.return_value = WorkflowResult(
            state=PartialTransition(output="switch_response"),
        )
        wf.context = context
        wf.outcome = outcome
        result = await wf.handle_step(
            step=step,
        )
        assert result == WorkflowResult(state=PartialTransition(output="switch_response"))


@test("task execution workflow: handle prompt step, unwrap is True")
async def _():
    wf = TaskExecutionWorkflow()
    step = PromptStep(prompt="hi there", unwrap=True)
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=uuid.uuid4(),
        ),
    )
    message = "Hello there"
    outcome = StepOutcome(output=message)
    wf.context = context
    wf.outcome = outcome
    with patch("agents_api.workflows.task_execution.workflow") as workflow:
        workflow.logger = Mock()
        workflow.execute_activity.return_value = "activity"

        assert await wf.handle_step(step=step) == WorkflowResult(
            state=PartialTransition(output=message),
        )
        workflow.execute_activity.assert_not_called()


@test("task execution workflow: handle prompt step, unwrap is False, autorun tools is False")
async def _():
    wf = TaskExecutionWorkflow()
    step = PromptStep(prompt="hi there", unwrap=False, auto_run_tools=False)
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=uuid.uuid4(),
        ),
    )
    message = {"choices": [{"finish_reason": "stop"}]}
    outcome = StepOutcome(output=message)
    wf.context = context
    wf.outcome = outcome
    with patch("agents_api.workflows.task_execution.workflow") as workflow:
        workflow.logger = Mock()
        workflow.execute_activity.return_value = "activity"

        assert await wf.handle_step(step=step) == WorkflowResult(
            state=PartialTransition(output=message),
        )
        workflow.execute_activity.assert_not_called()


@test(
    "task execution workflow: handle prompt step, unwrap is False, finish reason is not tool_calls",
)
async def _():
    wf = TaskExecutionWorkflow()
    step = PromptStep(prompt="hi there", unwrap=False)
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=uuid.uuid4(),
        ),
    )
    message = {"choices": [{"finish_reason": "stop"}]}
    outcome = StepOutcome(output=message)
    wf.context = context
    wf.outcome = outcome
    with patch("agents_api.workflows.task_execution.workflow") as workflow:
        workflow.logger = Mock()
        workflow.execute_activity.return_value = "activity"

        assert await wf.handle_step(step=step) == WorkflowResult(
            state=PartialTransition(output=message),
        )
        workflow.execute_activity.assert_not_called()


@test("task execution workflow: handle prompt step, function call")
async def _():
    async def _resp():
        return StepOutcome(output="function_call")

    wf = TaskExecutionWorkflow()
    step = PromptStep(prompt=[PromptItem(content="hi there", role="user")], auto_run_tools=True)
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=uuid.uuid4(),
        ),
    )
    message = {
        "choices": [
            {"finish_reason": "tool_calls", "message": {"tool_calls": [{"type": "function"}]}},
        ],
    }
    outcome = StepOutcome(output=message)
    wf.context = context
    wf.outcome = outcome
    with patch("agents_api.workflows.task_execution.workflow") as workflow:
        workflow.logger = Mock()
        workflow.execute_activity.side_effect = [_resp(), _resp()]

        assert await wf.handle_step(step=step) == WorkflowResult(
            state=PartialTransition(output="function_call", type="resume"),
        )
        workflow.execute_activity.assert_has_calls([
            call(
                task_steps.raise_complete_async,
                args=[context, [{"type": "function"}]],
                schedule_to_close_timeout=timedelta(days=31),
                retry_policy=DEFAULT_RETRY_POLICY,
                heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
            ),
            call(
                task_steps.prompt_step,
                context,
                schedule_to_close_timeout=timedelta(
                    seconds=30 if debug or testing else temporal_schedule_to_close_timeout,
                ),
                retry_policy=DEFAULT_RETRY_POLICY,
                heartbeat_timeout=timedelta(seconds=temporal_heartbeat_timeout),
            ),
        ])


@test("task execution workflow: evaluate foreach step expressions")
async def _():
    wf = TaskExecutionWorkflow()
    step = PromptStep(prompt=[PromptItem(content="hi there", role="user")])
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            task_id=uuid.uuid4(),
            status="running",
            input={"a": "1"},
        ),
    )
    scope_id = uuid.uuid4()
    wf.context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=scope_id,
        ),
    )
    with (
        patch(
            "agents_api.common.protocol.tasks.list_execution_inputs_data",
        ) as list_execution_inputs_data,
        patch(
            "agents_api.common.protocol.tasks.list_execution_state_data",
            return_value=[],
        ),
    ):
        list_execution_inputs_data.return_value = (
            Transition(
                id=uuid.uuid4(),
                execution_id=uuid.uuid4(),
                type="step",
                created_at=utcnow(),
                updated_at=utcnow(),
                output="output",
                current=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
                next=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
            ),
        )
        with patch(
            "agents_api.workflows.task_execution.base_evaluate_activity",
            new=base_evaluate,
        ):
            result = await wf.eval_step_exprs(
                ForeachStep(foreach=ForeachDo(in_="$ 1 + 2", do=YieldStep(workflow="wf1"))),
            )

        assert result == StepOutcome(output=3)


@test("task execution workflow: evaluate ifelse step expressions")
async def _():
    wf = TaskExecutionWorkflow()
    step = PromptStep(prompt=[PromptItem(content="hi there", role="user")])
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            task_id=uuid.uuid4(),
            status="running",
            input={"a": "1"},
        ),
    )
    scope_id = uuid.uuid4()
    wf.context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=scope_id,
        ),
    )
    with (
        patch(
            "agents_api.common.protocol.tasks.list_execution_inputs_data",
        ) as list_execution_inputs_data,
        patch(
            "agents_api.common.protocol.tasks.list_execution_state_data",
            return_value=[],
        ),
    ):
        list_execution_inputs_data.return_value = (
            Transition(
                id=uuid.uuid4(),
                execution_id=uuid.uuid4(),
                type="step",
                created_at=utcnow(),
                updated_at=utcnow(),
                output="output",
                current=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
                next=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
            ),
        )
        with patch(
            "agents_api.workflows.task_execution.base_evaluate_activity",
            new=base_evaluate,
        ):
            result = await wf.eval_step_exprs(
                IfElseWorkflowStep(if_="$ 1 + 2", then=YieldStep(workflow="wf1")),
            )

        assert result == StepOutcome(output=3)


@test("task execution workflow: evaluate return step expressions")
async def _():
    wf = TaskExecutionWorkflow()
    step = PromptStep(prompt=[PromptItem(content="hi there", role="user")])
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            task_id=uuid.uuid4(),
            status="running",
            input={"a": "1"},
        ),
    )
    scope_id = uuid.uuid4()
    wf.context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=scope_id,
        ),
    )
    with (
        patch(
            "agents_api.common.protocol.tasks.list_execution_inputs_data",
        ) as list_execution_inputs_data,
        patch(
            "agents_api.common.protocol.tasks.list_execution_state_data",
            return_value=[],
        ),
    ):
        list_execution_inputs_data.return_value = (
            Transition(
                id=uuid.uuid4(),
                execution_id=uuid.uuid4(),
                type="step",
                created_at=utcnow(),
                updated_at=utcnow(),
                output="output",
                current=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
                next=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
            ),
        )
        with patch(
            "agents_api.workflows.task_execution.base_evaluate_activity",
            new=base_evaluate,
        ):
            result = await wf.eval_step_exprs(
                ReturnStep(return_={"x": "$ 1 + 2"}),
            )

        assert result == StepOutcome(output={"x": 3})


@test("task execution workflow: evaluate wait for input step expressions")
async def _():
    wf = TaskExecutionWorkflow()
    step = PromptStep(prompt=[PromptItem(content="hi there", role="user")])
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            task_id=uuid.uuid4(),
            status="running",
            input={"a": "1"},
        ),
    )
    scope_id = uuid.uuid4()
    wf.context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=scope_id,
        ),
    )
    with (
        patch(
            "agents_api.common.protocol.tasks.list_execution_inputs_data",
        ) as list_execution_inputs_data,
        patch(
            "agents_api.common.protocol.tasks.list_execution_state_data",
            return_value=[],
        ),
    ):
        list_execution_inputs_data.return_value = (
            Transition(
                id=uuid.uuid4(),
                execution_id=uuid.uuid4(),
                type="step",
                created_at=utcnow(),
                updated_at=utcnow(),
                output="output",
                current=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
                next=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
            ),
        )
        with patch(
            "agents_api.workflows.task_execution.base_evaluate_activity",
            new=base_evaluate,
        ):
            result = await wf.eval_step_exprs(
                WaitForInputStep(wait_for_input=WaitForInputInfo(info={"x": "$ 1 + 2"})),
            )

        assert result == StepOutcome(output={"x": 3})


@test("task execution workflow: evaluate evaluate expressions")
async def _():
    wf = TaskExecutionWorkflow()
    step = PromptStep(prompt=[PromptItem(content="hi there", role="user")])
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            task_id=uuid.uuid4(),
            status="running",
            input={"a": "1"},
        ),
    )
    scope_id = uuid.uuid4()
    wf.context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=scope_id,
        ),
    )
    with (
        patch(
            "agents_api.common.protocol.tasks.list_execution_inputs_data",
        ) as list_execution_inputs_data,
        patch(
            "agents_api.common.protocol.tasks.list_execution_state_data",
            return_value=[],
        ),
    ):
        list_execution_inputs_data.return_value = (
            Transition(
                id=uuid.uuid4(),
                execution_id=uuid.uuid4(),
                type="step",
                created_at=utcnow(),
                updated_at=utcnow(),
                output="output",
                current=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
                next=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
            ),
        )
        with patch(
            "agents_api.workflows.task_execution.base_evaluate_activity",
            new=base_evaluate,
        ):
            result = await wf.eval_step_exprs(
                EvaluateStep(evaluate={"x": "$ 1 + 2"}),
            )

        assert result == StepOutcome(output={"x": 3})


@test("task execution workflow: evaluate map reduce expressions")
async def _():
    wf = TaskExecutionWorkflow()
    step = PromptStep(prompt=[PromptItem(content="hi there", role="user")])
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            task_id=uuid.uuid4(),
            status="running",
            input={"a": "1"},
        ),
    )
    scope_id = uuid.uuid4()
    wf.context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=scope_id,
        ),
    )
    with (
        patch(
            "agents_api.common.protocol.tasks.list_execution_inputs_data",
        ) as list_execution_inputs_data,
        patch(
            "agents_api.common.protocol.tasks.list_execution_state_data",
            return_value=[],
        ),
    ):
        list_execution_inputs_data.return_value = (
            Transition(
                id=uuid.uuid4(),
                execution_id=uuid.uuid4(),
                type="step",
                created_at=utcnow(),
                updated_at=utcnow(),
                output="output",
                current=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
                next=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
            ),
        )
        with patch(
            "agents_api.workflows.task_execution.base_evaluate_activity",
            new=base_evaluate,
        ):
            result = await wf.eval_step_exprs(
                MapReduceStep(over="$ 1 + 2", map=YieldStep(workflow="wf1")),
            )

        assert result == StepOutcome(output=3)


@test("task execution workflow: evaluate set expressions")
async def _():
    wf = TaskExecutionWorkflow()
    step = PromptStep(prompt=[PromptItem(content="hi there", role="user")])
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            task_id=uuid.uuid4(),
            status="running",
            input={"a": "1"},
        ),
    )
    scope_id = uuid.uuid4()
    wf.context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=scope_id,
        ),
    )
    with (
        patch(
            "agents_api.common.protocol.tasks.list_execution_inputs_data",
        ) as list_execution_inputs_data,
        patch(
            "agents_api.common.protocol.tasks.list_execution_state_data",
            return_value=[],
        ),
    ):
        list_execution_inputs_data.return_value = (
            Transition(
                id=uuid.uuid4(),
                execution_id=uuid.uuid4(),
                type="step",
                created_at=utcnow(),
                updated_at=utcnow(),
                output="output",
                current=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
                next=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
            ),
        )
        with patch(
            "agents_api.workflows.task_execution.base_evaluate_activity",
            new=base_evaluate,
        ):
            result = await wf.eval_step_exprs(SetStep(set={"x": "$ 1 + 2"}))

        assert result == StepOutcome(output={"x": 3})


@test("task execution workflow: evaluate log expressions")
async def _():
    wf = TaskExecutionWorkflow()
    step = PromptStep(prompt=[PromptItem(content="hi there", role="user")])
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            task_id=uuid.uuid4(),
            status="running",
            input={"a": "1"},
        ),
    )
    scope_id = uuid.uuid4()
    wf.context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=scope_id,
        ),
    )
    with (
        patch(
            "agents_api.common.protocol.tasks.list_execution_inputs_data",
        ) as list_execution_inputs_data,
        patch(
            "agents_api.common.protocol.tasks.list_execution_state_data",
            return_value=[],
        ),
    ):
        list_execution_inputs_data.return_value = (
            Transition(
                id=uuid.uuid4(),
                execution_id=uuid.uuid4(),
                type="step",
                created_at=utcnow(),
                updated_at=utcnow(),
                output={"x": "5"},
                current=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
                next=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
            ),
        )
        with patch(
            "agents_api.workflows.task_execution.base_evaluate_activity",
            new=base_evaluate,
        ):
            result = await wf.eval_step_exprs(LogStep(log="$ steps[0].input['x']"))

        assert result == StepOutcome(output="5")


@test("task execution workflow: evaluate switch expressions")
async def _():
    wf = TaskExecutionWorkflow()
    step = PromptStep(prompt=[PromptItem(content="hi there", role="user")])
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            task_id=uuid.uuid4(),
            status="running",
            input={"a": "1"},
        ),
    )
    scope_id = uuid.uuid4()
    wf.context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=scope_id,
        ),
    )
    with (
        patch(
            "agents_api.common.protocol.tasks.list_execution_inputs_data",
        ) as list_execution_inputs_data,
        patch(
            "agents_api.common.protocol.tasks.list_execution_state_data",
            return_value=[],
        ),
    ):
        list_execution_inputs_data.return_value = (
            Transition(
                id=uuid.uuid4(),
                execution_id=uuid.uuid4(),
                type="step",
                created_at=utcnow(),
                updated_at=utcnow(),
                output="output",
                current=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
                next=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
            ),
        )
        with patch(
            "agents_api.workflows.task_execution.base_evaluate_activity",
            new=base_evaluate,
        ):
            result = await wf.eval_step_exprs(
                SwitchStep(
                    switch=[
                        CaseThen(case="$ None", then=YieldStep(workflow="wf1")),
                        CaseThen(case="$ 1 + 3", then=YieldStep(workflow="wf2")),
                    ],
                ),
            )

        assert result == StepOutcome(output=1)


@test("task execution workflow: evaluate tool call expressions")
async def _():
    wf = TaskExecutionWorkflow()
    step = ToolCallStep(tool="tool1", arguments={"x": "$ 1 + 2"})
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[
                TaskToolDef(
                    name="tool1",
                    type="function",
                    spec={},
                ),
            ],
            workflows=[Workflow(name="main", steps=[step])],
        ),
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            task_id=uuid.uuid4(),
            status="running",
            input={"a": "1"},
        ),
    )
    scope_id = uuid.uuid4()
    wf.context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=scope_id,
        ),
    )
    with (
        patch(
            "agents_api.common.protocol.tasks.list_execution_inputs_data",
        ) as list_execution_inputs_data,
        patch(
            "agents_api.common.protocol.tasks.list_execution_state_data",
            return_value=[],
        ),
        patch("agents_api.workflows.task_execution.generate_call_id") as generate_call_id,
        patch("agents_api.common.protocol.tasks.workflow") as context_workflow,
        patch("agents_api.common.protocol.tasks.list_secrets_query") as mock_list_secrets,
    ):
        # Set up the mock to raise the expected exception
        context_workflow.execute_activity.side_effect = _NotInWorkflowEventLoopError(
            "Not in workflow event loop"
        )
        mock_list_secrets.return_value = []
        generate_call_id.return_value = "XXXX"
        list_execution_inputs_data.return_value = (
            Transition(
                id=uuid.uuid4(),
                execution_id=uuid.uuid4(),
                type="step",
                created_at=utcnow(),
                updated_at=utcnow(),
                output="output",
                current=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
                next=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
            ),
        )
        with patch(
            "agents_api.workflows.task_execution.base_evaluate_activity",
            new=base_evaluate,
        ):
            result = await wf.eval_step_exprs(
                ToolCallStep(tool="tool1", arguments={"x": "$ 1 + 2"}),
            )

        assert result == StepOutcome(
            output={
                "function": {"arguments": {"x": 3}, "name": "tool1"},
                "id": "XXXX",
                "type": "function",
            },
        )


@test("task execution workflow: evaluate yield expressions")
async def _():
    wf = TaskExecutionWorkflow()
    step = YieldStep(arguments={"x": "$ 1 + 2"}, workflow="main")
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            task_id=uuid.uuid4(),
            status="running",
            input={"a": "1"},
        ),
    )
    scope_id = uuid.uuid4()
    wf.context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=scope_id,
        ),
    )
    with (
        patch(
            "agents_api.common.protocol.tasks.list_execution_inputs_data",
        ) as list_execution_inputs_data,
        patch(
            "agents_api.common.protocol.tasks.list_execution_state_data",
            return_value=[],
        ),
    ):
        list_execution_inputs_data.return_value = (
            Transition(
                id=uuid.uuid4(),
                execution_id=uuid.uuid4(),
                type="step",
                created_at=utcnow(),
                updated_at=utcnow(),
                output="output",
                current=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
                next=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
            ),
        )
        with patch(
            "agents_api.workflows.task_execution.base_evaluate_activity",
            new=base_evaluate,
        ):
            result = await wf.eval_step_exprs(
                YieldStep(arguments={"x": "$ 1 + 2"}, workflow="main"),
            )

        scope_id = result.transition_to[1].scope_id

        assert result == StepOutcome(
            output={"x": 3},
            transition_to=(
                "step",
                TransitionTarget(step=0, workflow="main", scope_id=scope_id),
            ),
        )


@test("task execution workflow: evaluate yield expressions assertion")
async def _():
    wf = TaskExecutionWorkflow()
    step = ToolCallStep(tool="tool1", arguments={"x": "$ 1 + 2"})
    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            name="agent1",
        ),
        agent_tools=[],
        arguments={},
        task=TaskSpecDef(
            name="task1",
            tools=[],
            workflows=[Workflow(name="main", steps=[step])],
        ),
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            task_id=uuid.uuid4(),
            status="running",
            input={"a": "1"},
        ),
    )
    scope_id = uuid.uuid4()
    wf.context = StepContext(
        execution_input=execution_input,
        current_input="value 1",
        cursor=TransitionTarget(
            workflow="main",
            step=0,
            scope_id=scope_id,
        ),
    )
    with (
        patch(
            "agents_api.common.protocol.tasks.list_execution_inputs_data",
        ) as list_execution_inputs_data,
        patch(
            "agents_api.common.protocol.tasks.list_execution_state_data",
            return_value=[],
        ),
    ):
        list_execution_inputs_data.return_value = (
            Transition(
                id=uuid.uuid4(),
                execution_id=uuid.uuid4(),
                type="step",
                created_at=utcnow(),
                updated_at=utcnow(),
                output="output",
                current=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
                next=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=scope_id,
                ),
            ),
        )
        with (
            raises(AssertionError),
            patch(
                "agents_api.workflows.task_execution.base_evaluate_activity",
                new=base_evaluate,
            ),
        ):
            await wf.eval_step_exprs(YieldStep(arguments={"x": "$ 1 + 2"}, workflow="main"))

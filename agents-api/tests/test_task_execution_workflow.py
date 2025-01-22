import uuid
from unittest.mock import Mock, patch

from agents_api.autogen.openapi_model import (
    Agent,
    CaseThen,
    GetStep,
    SwitchStep,
    TaskSpecDef,
    TaskToolDef,
    ToolCallStep,
    TransitionTarget,
    Workflow,
)
from agents_api.common.protocol.tasks import (
    ExecutionInput,
    PartialTransition,
    StepContext,
    StepOutcome,
)
from agents_api.common.utils.datetime import utcnow
from agents_api.workflows.task_execution import TaskExecutionWorkflow
from temporalio import activity
from temporalio.client import Client
from temporalio.exceptions import ApplicationError
from temporalio.worker import Worker
from ward import skip, test

from .fixtures import temporal_client


@activity.defn(name="return_step")
async def return_step_mocked(context: StepContext) -> str:
    return "finish"


@skip
@test("task execution workflow: return step")
async def _(client: Client = temporal_client):
    task_queue_name = str(uuid.uuid4())
    async with Worker(
        client,
        task_queue=task_queue_name,
        workflows=[TaskExecutionWorkflow],
        activities=[
            return_step_mocked,
        ],
    ):
        # TODO: set correct values
        execution_input = ExecutionInput()
        start = 0
        previous_inputs = []
        assert (
            await client.execute_workflow(
                TaskExecutionWorkflow.run,
                args=[execution_input, start, previous_inputs],
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )
            == "finish"
        )


@test("task execution workflow: handle function tool call step")
async def _():
    async def _resp():
        return "function_tool_call_response"

    wf = TaskExecutionWorkflow()
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
            workflows=[Workflow(name="main", steps=[ToolCallStep(tool="tool1")])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        inputs=["value 1"],
        cursor=TransitionTarget(
            workflow="main",
            step=0,
        ),
    )
    step = ToolCallStep(tool="tool1")
    outcome = StepOutcome(output={"type": "function"})
    with patch("agents_api.workflows.task_execution.workflow") as workflow:
        workflow.execute_activity.return_value = _resp()
        result = await wf.handle_step(
            context=context,
            step=step,
            outcome=outcome,
        )
        assert result == PartialTransition(type="resume", output="function_tool_call_response")


@test("task execution workflow: handle integration tool call step")
async def _():
    async def _resp():
        return "integration_tool_call_response"

    wf = TaskExecutionWorkflow()
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
            workflows=[Workflow(name="main", steps=[ToolCallStep(tool="tool1")])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        inputs=["value 1"],
        cursor=TransitionTarget(
            workflow="main",
            step=0,
        ),
    )
    step = ToolCallStep(tool="tool1")
    outcome = StepOutcome(
        output={"type": "integration", "integration": {"name": "tool1", "arguments": {}}}
    )
    with patch("agents_api.workflows.task_execution.workflow") as workflow:
        workflow.execute_activity.return_value = _resp()
        result = await wf.handle_step(
            context=context,
            step=step,
            outcome=outcome,
        )
        assert result == PartialTransition(output="integration_tool_call_response")


@test("task execution workflow: handle api_call tool call step")
async def _():
    async def _resp():
        return "api_call_tool_call_response"

    wf = TaskExecutionWorkflow()
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
            workflows=[Workflow(name="main", steps=[ToolCallStep(tool="tool1")])],
        ),
    )
    context = StepContext(
        execution_input=execution_input,
        inputs=["value 1"],
        cursor=TransitionTarget(
            workflow="main",
            step=0,
        ),
    )
    step = ToolCallStep(tool="tool1")
    outcome = StepOutcome(output={"type": "function"})
    with patch("agents_api.workflows.task_execution.workflow") as workflow:
        workflow.execute_activity.return_value = _resp()
        result = await wf.handle_step(
            context=context,
            step=step,
            outcome=outcome,
        )
        assert result == PartialTransition(type="resume", output="api_call_tool_call_response")


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
        inputs=["value 1"],
        cursor=TransitionTarget(
            workflow="main",
            step=0,
        ),
    )
    outcome = StepOutcome(output=1)
    with patch(
        "agents_api.workflows.task_execution.execute_switch_branch"
    ) as execute_switch_branch:
        execute_switch_branch.return_value = "switch_response"
        result = await wf.handle_step(
            context=context,
            step=step,
            outcome=outcome,
        )
        assert result == PartialTransition(output="switch_response")


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
        inputs=["value 1"],
        cursor=TransitionTarget(
            workflow="main",
            step=0,
        ),
    )
    outcome = StepOutcome(output=-1)
    with patch("agents_api.workflows.task_execution.workflow") as workflow:
        workflow.logger = Mock()
        try:
            await wf.handle_step(
                context=context,
                step=step,
                outcome=outcome,
            )
        except Exception as e:
            print("-->", type(e))
            assert isinstance(e, ApplicationError)
        else:
            assert False

import uuid
from datetime import timedelta
from unittest.mock import Mock, call, patch

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
from temporalio.exceptions import ApplicationError
from ward import raises, test


@test("utility: prepare_for_step - underscore")
async def _():
    with patch("agents_api.common.protocol.tasks.StepContext.get_inputs", return_value=([{"x": "1"}, {"y": "2"}, {"z": "3"}], ["", "first step", "second step"])):
        
        step = ToolCallStep(tool="tool1")
        context = StepContext(
            execution_input=ExecutionInput(
                developer_id=uuid.uuid4(),
                agent=Agent(id=uuid.uuid4(), name="test agent", created_at=utcnow(), updated_at=utcnow()),
                agent_tools=[],
                arguments={},        
                task=TaskSpecDef(
                    name="task1",
                    tools=[],
                    workflows=[Workflow(name="main", steps=[step])],
                ),
            ),
            current_input={"current_input": "value 1"},
            cursor=TransitionTarget(
                workflow="main",
                step=0,
            ),
        )
        result = await context.prepare_for_step()
        assert result["_"] == {"current_input": "value 1"}

@test("utility: prepare_for_step - label lookup in step")
async def _():
    with patch("agents_api.common.protocol.tasks.StepContext.get_inputs", return_value=([{"x": "1"}, {"y": "2"}, {"z": "3"}], ["", "first step", "second step"])):
        
        step = ToolCallStep(tool="tool1")
        context = StepContext(
            execution_input=ExecutionInput(
                developer_id=uuid.uuid4(),
                agent=Agent(id=uuid.uuid4(), name="test agent", created_at=utcnow(), updated_at=utcnow()),
                agent_tools=[],
                arguments={},        
                task=TaskSpecDef(
                    name="task1",
                    tools=[],
                    workflows=[Workflow(name="main", steps=[step])],
                ),
            ),
            current_input={"current_input": "value 1"},
            cursor=TransitionTarget(
                workflow="main",
                step=0,
            ),
        )
        result = await context.prepare_for_step()

        assert result["steps"]["first step"]["input"] == {"x": "1"}
        assert result["steps"]["first step"]["output"] == {"y": "2"}
        assert result["steps"]["second step"]["input"] == {"y": "2"}
        assert result["steps"]["second step"]["output"] == {"z": "3"}

@test("utility: prepare_for_step - stepx")
async def _():
    with patch("agents_api.common.protocol.tasks.StepContext.get_inputs", return_value=([{"x": "1"}, {"y": "2"}, {"z": "3"}], ["", "first step", "second step"])):
        
        step = ToolCallStep(tool="tool1")
        context = StepContext(
            execution_input=ExecutionInput(
                developer_id=uuid.uuid4(),
                agent=Agent(id=uuid.uuid4(), name="test agent", created_at=utcnow(), updated_at=utcnow()),
                agent_tools=[],
                arguments={},        
                task=TaskSpecDef(
                    name="task1",
                    tools=[],
                    workflows=[Workflow(name="main", steps=[step])],
                ),
            ),
            current_input={"current_input": "value 1"},
            cursor=TransitionTarget(
                workflow="main",
                step=0,
            ),
        )
        result = await context.prepare_for_step()

        assert result["step0"] == {"x": "1"}
        assert result["step1"] == {"y": "2"}
        assert result["step2"] == {"z": "3"}

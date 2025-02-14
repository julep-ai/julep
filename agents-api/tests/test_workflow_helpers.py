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
from agents_api.workflows.task_execution.helpers import execute_map_reduce_step_parallel


@test("execute_map_reduce_step_parallel: subworkflow step not supported")
async def _():
    async def _resp():
        return "response"

    subworkflow_step = YieldStep(kind_="yield", workflow='subworkflow', arguments={'test': '$ _'})

    step = MapReduceStep(
        kind_="map_reduce",
        map=subworkflow_step,
        over="$ [1, 2, 3]",
        parallelism=3,
    )

    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(), name="test agent", created_at=utcnow(), updated_at=utcnow()
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
        current_input={"current_input": "value 1"},
        cursor=TransitionTarget(
            workflow="main",
            step=0,
        ),
    )
    with patch("agents_api.workflows.task_execution.helpers.workflow") as workflow:
        workflow.execute_activity.return_value = await _resp()
        with raises(ValueError):
            await execute_map_reduce_step_parallel(
                context=context,
                map_defn=step.map,
                execution_input=execution_input,
                items=["1", "2", "3"],
                current_input={},
            )

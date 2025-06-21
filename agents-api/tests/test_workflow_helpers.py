import uuid
from unittest.mock import AsyncMock, patch

from agents_api.autogen.openapi_model import (
    Agent,
    Execution,
    MapReduceStep,
    PromptItem,
    PromptStep,
    TaskSpecDef,
    TransitionTarget,
    Workflow,
)
from agents_api.common.protocol.tasks import (
    ExecutionInput,
    PartialTransition,
    StepContext,
    WorkflowResult,
)
from agents_api.common.utils.datetime import utcnow
from agents_api.workflows.task_execution.helpers import execute_map_reduce_step_parallel
import pytest


async def test_execute_map_reduce_step_parallel_parallelism_must_be_greater_than_1():
    async def _resp():
        return "response"

    subworkflow_step = PromptStep(prompt=[PromptItem(content="hi there", role="user")])

    step = MapReduceStep(
        kind_="map_reduce",
        map=subworkflow_step,
        over="$ [1, 2, 3]",
        parallelism=1,
    )

    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            name="test agent",
            created_at=utcnow(),
            updated_at=utcnow(),
        ),
        agent_tools=[],
        arguments={},
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            status="running",
            task_id=uuid.uuid4(),
            input={},
        ),
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
            scope_id=uuid.uuid4(),
        ),
    )
    with (
        patch("agents_api.workflows.task_execution.helpers.workflow") as workflow,
        patch("agents_api.workflows.task_execution.helpers.continue_as_child"),
        # Also patch execute_map_reduce_step as it gets called when parallelism is 1
        patch(
            "agents_api.workflows.task_execution.helpers.execute_map_reduce_step"
        ) as execute_map_reduce_step_mock,
    ):
        # This is the function that gets called when parallelism is 1
        execute_map_reduce_step_mock.side_effect = AssertionError(
            "Parallelism must be greater than 1"
        )

        # Mock run function that will be returned by lambda in continue_as_child
        run_mock = AsyncMock()

        # Mock lambda that creates child workflow or continue as new
        workflow.continue_as_new = run_mock
        workflow.execute_child_workflow.return_value = run_mock
        workflow.execute_activity.return_value = _resp()

        with pytest.raises(AssertionError):
            await execute_map_reduce_step_parallel(
                context=context,
                map_defn=step.map,
                execution_input=execution_input,
                items=["1", "2", "3"],
                current_input={},
                parallelism=1,
            )


async def test_execute_map_reduce_step_parallel_returned_true():
    async def _resp():
        return "response"

    # Create the workflow results we'll use
    result1 = WorkflowResult(
        returned=False,
        state=PartialTransition(output="response 1"),
    )

    result2 = WorkflowResult(
        returned=True,
        state=PartialTransition(output="response 2"),
    )

    subworkflow_step = PromptStep(prompt=[PromptItem(content="hi there", role="user")])

    step = MapReduceStep(
        kind_="map_reduce",
        map=subworkflow_step,
        over="$ [1, 2]",
        parallelism=100,
    )

    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            name="test agent",
            created_at=utcnow(),
            updated_at=utcnow(),
        ),
        agent_tools=[],
        arguments={},
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            status="running",
            task_id=uuid.uuid4(),
            input={},
        ),
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
            scope_id=uuid.uuid4(),
        ),
    )
    with (
        patch("agents_api.workflows.task_execution.helpers.workflow") as workflow,
        patch(
            "agents_api.workflows.task_execution.helpers.continue_as_child"
        ) as continue_as_child_mock,
    ):
        # Mock continue_as_child directly to return our workflow results
        # First call returns result1, second call returns result2
        continue_as_child_mock.side_effect = [result1, result2]
        workflow.execute_activity.return_value = _resp()

        result = await execute_map_reduce_step_parallel(
            context=context,
            map_defn=step.map,
            execution_input=execution_input,
            items=[1, 2],
            current_input={},
            parallelism=100,
        )

        workflow_result = WorkflowResult(
            returned=True,
            state=PartialTransition(output="response 2"),
        )

        assert result == workflow_result


async def test_execute_map_reduce_step_parallel_returned_false():
    async def _resp():
        return ["response 1", "response 2"]

    # Create the workflow results we'll use
    result1 = WorkflowResult(
        returned=False,
        state=PartialTransition(output="response 1"),
    )

    result2 = WorkflowResult(
        returned=False,
        state=PartialTransition(output="response 2"),
    )

    subworkflow_step = PromptStep(prompt=[PromptItem(content="hi there", role="user")])

    step = MapReduceStep(
        kind_="map_reduce",
        map=subworkflow_step,
        over="$ [1, 2]",
        parallelism=100,
    )

    execution_input = ExecutionInput(
        developer_id=uuid.uuid4(),
        agent=Agent(
            id=uuid.uuid4(),
            name="test agent",
            created_at=utcnow(),
            updated_at=utcnow(),
        ),
        agent_tools=[],
        arguments={},
        execution=Execution(
            id=uuid.uuid4(),
            created_at=utcnow(),
            updated_at=utcnow(),
            status="running",
            task_id=uuid.uuid4(),
            input={},
        ),
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
            scope_id=uuid.uuid4(),
        ),
    )
    with (
        patch("agents_api.workflows.task_execution.helpers.workflow") as workflow,
        patch(
            "agents_api.workflows.task_execution.helpers.continue_as_child"
        ) as continue_as_child_mock,
    ):
        # Mock continue_as_child directly to return our workflow results
        # First call returns result1, second call returns result2
        continue_as_child_mock.side_effect = [result1, result2]
        workflow.execute_activity.return_value = _resp()

        result = await execute_map_reduce_step_parallel(
            context=context,
            map_defn=step.map,
            execution_input=execution_input,
            items=[1, 2],
            current_input={},
            parallelism=100,
        )

        workflow_result = WorkflowResult(
            returned=False,
            state=PartialTransition(output=["response 1", "response 2"]),
        )

        assert result == workflow_result

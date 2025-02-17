import uuid
from unittest.mock import patch

from agents_api.autogen.openapi_model import (
    Agent,
    TaskSpecDef,
    ToolCallStep,
    Transition,
    TransitionTarget,
    Workflow,
)
from agents_api.common.protocol.tasks import (
    ExecutionInput,
    StepContext,
)
from agents_api.common.utils.datetime import utcnow
from agents_api.common.utils.workflows import get_workflow_name
from ward import raises, test


@test("utility: prepare_for_step - underscore")
async def _():
    with patch(
        "agents_api.common.protocol.tasks.StepContext.get_inputs",
        return_value=(
            [{"x": "1"}, {"y": "2"}, {"z": "3"}],
            [None, "first step", "second step"],
            {}
        ),
    ):
        step = ToolCallStep(tool="tool1")
        context = StepContext(
            execution_input=ExecutionInput(
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
    with patch(
        "agents_api.common.protocol.tasks.StepContext.get_inputs",
        return_value=(
            [{"x": "1"}, {"y": "2"}, {"z": "3"}],
            [None, "first step", "second step"],
            {}
        ),
    ):
        step = ToolCallStep(tool="tool1")
        context = StepContext(
            execution_input=ExecutionInput(
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


@test("utility: get_workflow_name")
async def _():
    transition = Transition(
        id=uuid.uuid4(),
        execution_id=uuid.uuid4(),
        output=None,
        created_at=utcnow(),
        updated_at=utcnow(),
        type="step",
        current=TransitionTarget(workflow="main", step=0),
        next=TransitionTarget(workflow="main", step=1),
    )

    transition.current = TransitionTarget(workflow="main", step=0)
    transition.next = TransitionTarget(workflow="main", step=1)
    assert get_workflow_name(transition) == "main"

    transition.current = TransitionTarget(workflow="`main`[0].if_else.then", step=0)
    transition.next = None
    assert get_workflow_name(transition) == "main"

    transition.current = TransitionTarget(workflow="subworkflow", step=0)
    transition.next = TransitionTarget(workflow="subworkflow", step=1)
    assert get_workflow_name(transition) == "subworkflow"

    transition.current = TransitionTarget(workflow="`subworkflow`[0].if_else.then", step=0)
    transition.next = TransitionTarget(workflow="`subworkflow`[0].if_else.else", step=1)
    assert get_workflow_name(transition) == "subworkflow"

    transition.current = TransitionTarget(workflow="PAR:`main`[2].mapreduce[0][2],0", step=0)
    transition.next = None
    assert get_workflow_name(transition) == "main"

    transition.current = TransitionTarget(
        workflow="PAR:`subworkflow`[2].mapreduce[0][3],0", step=0
    )
    transition.next = None
    assert get_workflow_name(transition) == "subworkflow"


@test("utility: get_workflow_name - raises")
async def _():
    transition = Transition(
        id=uuid.uuid4(),
        execution_id=uuid.uuid4(),
        output=None,
        created_at=utcnow(),
        updated_at=utcnow(),
        type="step",
        current=TransitionTarget(workflow="main", step=0),
        next=TransitionTarget(workflow="main", step=1),
    )

    with raises(AssertionError):
        transition.current = TransitionTarget(workflow="`main[2].mapreduce[0][2],0", step=0)
        get_workflow_name(transition)

    with raises(AssertionError):
        transition.current = TransitionTarget(workflow="PAR:`", step=0)
        get_workflow_name(transition)

    with raises(AssertionError):
        transition.current = TransitionTarget(workflow="`", step=0)
        get_workflow_name(transition)

    with raises(AssertionError):
        transition.current = TransitionTarget(
            workflow="PAR:`subworkflow[2].mapreduce[0][3],0", step=0
        )
        get_workflow_name(transition)

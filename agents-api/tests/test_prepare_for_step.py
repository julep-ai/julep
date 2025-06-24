import uuid
from unittest.mock import patch

import pytest
from agents_api.autogen.openapi_model import (
    Agent,
    Execution,
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
from uuid_extensions import uuid7

from tests.utils import generate_transition


async def test_utility_prepare_for_step_underscore():
    with patch(
        "agents_api.common.protocol.tasks.StepContext.get_inputs",
        return_value=(
            [{"x": "1"}, {"y": "2"}, {"z": "3"}],
            [None, "first step", "second step"],
            {},
        ),
    ):
        step = ToolCallStep(tool="tool1")
        context = StepContext(
            execution_input=ExecutionInput(
                developer_id=uuid.uuid4(),
                agent=Agent(
                    id=uuid.uuid4(),
                    name="test agent",
                    created_at=utcnow(),
                    updated_at=utcnow(),
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
                scope_id=uuid.uuid4(),
            ),
        )
        result = await context.prepare_for_step()
        assert result["_"] == {"current_input": "value 1"}


async def test_utility_prepare_for_step_label_lookup_in_step():
    with patch(
        "agents_api.common.protocol.tasks.StepContext.get_inputs",
        return_value=(
            [{"x": "1"}, {"y": "2"}, {"z": "3"}],
            [None, "first step", "second step"],
            {},
        ),
    ):
        step = ToolCallStep(tool="tool1")
        context = StepContext(
            execution_input=ExecutionInput(
                developer_id=uuid.uuid4(),
                agent=Agent(
                    id=uuid.uuid4(),
                    name="test agent",
                    created_at=utcnow(),
                    updated_at=utcnow(),
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
                scope_id=uuid.uuid4(),
            ),
        )
        result = await context.prepare_for_step()

        assert result["steps"]["first step"]["input"] == {"x": "1"}
        assert result["steps"]["first step"]["output"] == {"y": "2"}
        assert result["steps"]["second step"]["input"] == {"y": "2"}
        assert result["steps"]["second step"]["output"] == {"z": "3"}


async def test_utility_prepare_for_step_global_state():
    with patch(
        "agents_api.common.protocol.tasks.StepContext.get_inputs",
        return_value=([], [], {"user_name": "John", "count": 10, "has_data": True}),
    ):
        step = ToolCallStep(tool="tool1")
        context = StepContext(
            execution_input=ExecutionInput(
                developer_id=uuid.uuid4(),
                agent=Agent(
                    id=uuid.uuid4(),
                    name="test agent",
                    created_at=utcnow(),
                    updated_at=utcnow(),
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
                scope_id=uuid.uuid4(),
            ),
        )
        result = await context.prepare_for_step()
        assert result["state"]["user_name"] == "John"
        assert result["state"]["count"] == 10
        assert result["state"]["has_data"] is True


async def test_utility_get_workflow_name():
    transition = Transition(
        id=uuid.uuid4(),
        execution_id=uuid.uuid4(),
        output=None,
        created_at=utcnow(),
        updated_at=utcnow(),
        type="step",
        current=TransitionTarget(workflow="main", step=0, scope_id=uuid.uuid4()),
        next=TransitionTarget(workflow="main", step=1, scope_id=uuid.uuid4()),
    )

    transition.current = TransitionTarget(
        workflow="main", step=0, scope_id=uuid.uuid4()
    )
    transition.next = TransitionTarget(workflow="main", step=1, scope_id=uuid.uuid4())
    assert get_workflow_name(transition) == "main"

    transition.current = TransitionTarget(
        workflow="`main`[0].if_else.then",
        step=0,
        scope_id=uuid.uuid4(),
    )
    transition.next = None
    assert get_workflow_name(transition) == "main"

    transition.current = TransitionTarget(
        workflow="subworkflow", step=0, scope_id=uuid.uuid4()
    )
    transition.next = TransitionTarget(
        workflow="subworkflow", step=1, scope_id=uuid.uuid4()
    )
    assert get_workflow_name(transition) == "subworkflow"

    transition.current = TransitionTarget(
        workflow="`subworkflow`[0].if_else.then",
        step=0,
        scope_id=uuid.uuid4(),
    )
    transition.next = TransitionTarget(
        workflow="`subworkflow`[0].if_else.else",
        step=1,
        scope_id=uuid.uuid4(),
    )
    assert get_workflow_name(transition) == "subworkflow"

    transition.current = TransitionTarget(
        workflow="PAR:`main`[2].mapreduce[0][2],0",
        step=0,
        scope_id=uuid.uuid4(),
    )
    transition.next = None
    assert get_workflow_name(transition) == "main"

    transition.current = TransitionTarget(
        workflow="PAR:`subworkflow`[2].mapreduce[0][3],0",
        step=0,
        scope_id=uuid.uuid4(),
    )
    transition.next = None
    assert get_workflow_name(transition) == "subworkflow"


async def test_utility_get_workflow_name_raises():
    transition = Transition(
        id=uuid.uuid4(),
        execution_id=uuid.uuid4(),
        output=None,
        created_at=utcnow(),
        updated_at=utcnow(),
        type="step",
        current=TransitionTarget(workflow="main", step=0, scope_id=uuid.uuid4()),
        next=TransitionTarget(workflow="main", step=1, scope_id=uuid.uuid4()),
    )

    with pytest.raises(AssertionError):
        transition.current = TransitionTarget(
            workflow="`main[2].mapreduce[0][2],0",
            step=0,
            scope_id=uuid.uuid4(),
        )
        get_workflow_name(transition)

    with pytest.raises(AssertionError):
        transition.current = TransitionTarget(
            workflow="PAR:`", step=0, scope_id=uuid.uuid4()
        )
        get_workflow_name(transition)

    with pytest.raises(AssertionError):
        transition.current = TransitionTarget(
            workflow="`", step=0, scope_id=uuid.uuid4()
        )
        get_workflow_name(transition)

    with pytest.raises(AssertionError):
        transition.current = TransitionTarget(
            workflow="PAR:`subworkflow[2].mapreduce[0][3],0",
            step=0,
            scope_id=uuid.uuid4(),
        )
        get_workflow_name(transition)


async def test_utility_get_inputs_2_parallel_subworkflows():
    uuid7()
    subworkflow1_scope_id = uuid7()
    subworkflow2_scope_id = uuid7()

    transition1 = generate_transition(
        type="init_branch",
        output={"b": 1},
        current_step=TransitionTarget(
            workflow="subworkflow",
            step=0,
            scope_id=subworkflow1_scope_id,
        ),
        next_step=TransitionTarget(
            workflow="subworkflow",
            step=0,
            scope_id=subworkflow1_scope_id,
        ),
    )

    transition2 = generate_transition(
        type="step",
        output={"c": 1},
        current_step=TransitionTarget(
            workflow="subworkflow",
            step=0,
            scope_id=subworkflow1_scope_id,
        ),
        next_step=TransitionTarget(
            workflow="subworkflow",
            step=1,
            scope_id=subworkflow1_scope_id,
        ),
    )

    subworkflow1_transitions = [transition1, transition2]

    transition3 = generate_transition(
        type="init_branch",
        output={"b": 2},
        current_step=TransitionTarget(
            workflow="subworkflow",
            step=0,
            scope_id=subworkflow2_scope_id,
        ),
        next_step=TransitionTarget(
            workflow="subworkflow",
            step=0,
            scope_id=subworkflow2_scope_id,
        ),
    )

    transition4 = generate_transition(
        type="step",
        output={"c": 2},
        current_step=TransitionTarget(
            workflow="subworkflow",
            step=0,
            scope_id=subworkflow2_scope_id,
        ),
        next_step=TransitionTarget(
            workflow="subworkflow",
            step=1,
            scope_id=subworkflow2_scope_id,
        ),
    )

    subworkflow2_transitions = [transition3, transition4]

    step = ToolCallStep(tool="tool1")
    context = StepContext(
        execution_input=ExecutionInput(
            developer_id=uuid.uuid4(),
            agent=Agent(
                id=uuid.uuid4(),
                name="test agent",
                created_at=utcnow(),
                updated_at=utcnow(),
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
                task_id=uuid.uuid4(),
                created_at=utcnow(),
                updated_at=utcnow(),
                status="running",
                input={},
            ),
        ),
        current_input={"current_input": "value 1"},
        cursor=TransitionTarget(
            workflow="subworkflow",
            step=1,
            scope_id=uuid7(),
        ),
    )

    with (
        patch(
            "agents_api.common.protocol.tasks.list_execution_inputs_data",
            return_value=subworkflow1_transitions,
        ),
        patch(
            "agents_api.common.protocol.tasks.list_execution_state_data",
            return_value=[],
        ),
    ):
        context.cursor.scope_id = subworkflow1_scope_id
        inputs, labels, state = await context.get_inputs()
        assert inputs == [{"b": 1}, {"c": 1}]
        assert labels == [None, None]
        assert state == {}

    with (
        patch(
            "agents_api.common.protocol.tasks.list_execution_inputs_data",
            return_value=subworkflow2_transitions,
        ),
        patch(
            "agents_api.common.protocol.tasks.list_execution_state_data",
            return_value=[],
        ),
    ):
        context.cursor.scope_id = subworkflow2_scope_id
        inputs, labels, state = await context.get_inputs()
        assert inputs == [{"b": 2}, {"c": 2}]
        assert labels == [None, None]
        assert state == {}

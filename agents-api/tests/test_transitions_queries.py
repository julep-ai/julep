"""Tests for transitions queries."""


from agents_api.autogen.openapi_model import CreateTransitionRequest
from agents_api.clients.pg import create_db_pool
from agents_api.queries.executions import list_execution_inputs_data, list_execution_state_data
from agents_api.queries.executions.create_execution_transition import (
    create_execution_transition,
)
from ward import test

from tests.fixtures import custom_scope_id, pg_dsn, test_developer_id, test_execution_started


@test("query: list execution inputs data")
async def _(
    dsn=pg_dsn,
    developer_id=test_developer_id,
    scope_id=custom_scope_id,
    execution_started=test_execution_started,
):
    pool = await create_db_pool(dsn=dsn)
    execution = execution_started

    data = []

    for i in range(10):
        data.append(
            CreateTransitionRequest(
                type="init_branch",
                output=i + 1,
                current={
                    "workflow": f"`main`[0].foreach[{max(0, i - 1)}]",
                    "step": 0,
                    "scope_id": scope_id,
                },
                next={"workflow": f"`main`[0].foreach[{i}]", "step": 0, "scope_id": scope_id},
            )
        )

        data.append(
            CreateTransitionRequest(
                type="finish_branch",
                output={"inside_foreach": f"inside foreach {i}"},
                current={
                    "workflow": f"`main`[0].foreach[{i}]",
                    "step": 0,
                    "scope_id": scope_id,
                },
                next=None,
            )
        )

    data.append(
        CreateTransitionRequest(
            type="step",
            output=[{"inside_foreach": "inside foreach"}],
            current={"workflow": "main", "step": 0, "scope_id": scope_id},
            next={"workflow": "main", "step": 1, "scope_id": scope_id},
        )
    )

    data.append(
        CreateTransitionRequest(
            type="step",
            output={"inside_evaluate": "inside evaluate"},
            current={"workflow": "main", "step": 1, "scope_id": scope_id},
            next={"workflow": "main", "step": 2, "scope_id": scope_id},
        )
    )

    data.append(
        CreateTransitionRequest(
            type="finish",
            output={"final_step": "final step"},
            current={"workflow": "main", "step": 2, "scope_id": scope_id},
            next=None,
        )
    )

    for transition in data:
        await create_execution_transition(
            developer_id=developer_id,
            execution_id=execution.id,
            data=transition,
            connection_pool=pool,
        )

    transitions = await list_execution_inputs_data(
        execution_id=execution.id,
        scope_id=scope_id,
        direction="asc",
        connection_pool=pool,
    )

    for transition in transitions:
        print(f"transition: {transition}")

    assert len(transitions) == 3
    assert transitions[1].output == [{"inside_foreach": "inside foreach"}]
    assert transitions[2].output == {"inside_evaluate": "inside evaluate"}


@test("query: list execution state data")
async def _(
    dsn=pg_dsn, 
    developer_id=test_developer_id, 
    scope_id=custom_scope_id,
    execution_started=test_execution_started,
):
    pool = await create_db_pool(dsn=dsn)
    execution = execution_started

    data = []

    data.append(CreateTransitionRequest(
        type="step",
        output={"set_step": "set step"},
        current={"workflow": "main", "step": 0, "scope_id": scope_id},
        next={"workflow": "main", "step": 1, "scope_id": scope_id},
        metadata={"step_type": "SetStep"},
    ))

    data.append(CreateTransitionRequest(
        type="finish",
        output={"final_step": "final step"},
        current={"workflow": "main", "step": 1, "scope_id": scope_id},
        next=None,
    ))

    for transition in data:
        await create_execution_transition(
            developer_id=developer_id,
            execution_id=execution.id,
            data=transition,
            connection_pool=pool,
        )

    transitions = await list_execution_state_data(
        execution_id=execution.id,
        scope_id=scope_id,
        direction="asc",
        connection_pool=pool,
    )

    for transition in transitions:
        print(f"transition: {transition}")

    assert len(transitions) == 1
    assert transitions[0].output == {'set_step': 'set step'}
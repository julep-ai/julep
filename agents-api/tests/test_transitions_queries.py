"""Tests for transitions queries."""

from datetime import timedelta
from uuid import UUID

from agents_api.autogen.openapi_model import CreateTransitionRequest
from agents_api.clients.pg import create_db_pool
from agents_api.common.utils.datetime import datetime, utcnow
from agents_api.queries.executions import (
    list_execution_inputs_data,
    list_execution_state_data,
)
from agents_api.queries.executions.create_execution_transition import (
    create_execution_transition,
)
from asyncpg import Pool
from uuid_extensions import uuid7


async def test_query_list_execution_inputs_data(
    pg_dsn,
    test_developer_id,
    custom_scope_id,
    test_execution_started,
):
    pool = await create_db_pool(dsn=pg_dsn)
    execution = test_execution_started
    scope_id = custom_scope_id

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
                next={
                    "workflow": f"`main`[0].foreach[{i}]",
                    "step": 0,
                    "scope_id": scope_id,
                },
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
            developer_id=test_developer_id,
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

    assert len(transitions) == 3
    assert transitions[0].output == {}
    assert transitions[1].output == [{"inside_foreach": "inside foreach"}]
    assert transitions[2].output == {"inside_evaluate": "inside evaluate"}


async def test_query_list_execution_state_data(
    pg_dsn,
    test_developer_id,
    custom_scope_id,
    test_execution_started,
):
    pool = await create_db_pool(dsn=pg_dsn)
    execution = test_execution_started
    scope_id = custom_scope_id

    data = []

    data.append(
        CreateTransitionRequest(
            type="step",
            output={"set_step": "set step"},
            current={"workflow": "main", "step": 0, "scope_id": scope_id},
            next={"workflow": "main", "step": 1, "scope_id": scope_id},
            metadata={"step_type": "SetStep"},
        )
    )

    data.append(
        CreateTransitionRequest(
            type="finish",
            output={"final_step": "final step"},
            current={"workflow": "main", "step": 1, "scope_id": scope_id},
            next=None,
        )
    )

    for transition in data:
        await create_execution_transition(
            developer_id=test_developer_id,
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

    assert len(transitions) == 1
    assert transitions[0].output == {"set_step": "set step"}


async def create_execution(
    pool: Pool,
    developer_id: UUID,
    task_id: UUID,
    created_at: datetime,
):
    execution_id = uuid7()
    create_execution_query = """
        INSERT INTO executions
        (
            developer_id,
            task_id,
            execution_id,
            input,
            metadata,
            task_version,
            created_at
        )
        VALUES
        (
            $1,
            $2,
            $3,
            $4,
            $5,
            1,
            $6
        )
        RETURNING *;
    """

    await pool.fetchrow(
        create_execution_query,
        str(developer_id),
        str(task_id),
        str(execution_id),
        {"test": "test"},
        {},
        created_at,
    )

    return execution_id


async def create_transition(
    pool: Pool,
    execution_id: UUID,
    type: str,
    current_step: dict,
    next_step: dict,
    output: dict,
    metadata: dict,
    created_at: datetime,
):
    create_execution_transition_query = """
        INSERT INTO transitions
        (
            execution_id,
            transition_id,
            type,
            step_label,
            current_step,
            next_step,
            output,
            task_token,
            metadata,
            created_at
        )
        VALUES
        (
            $1,
            $2,
            $3,
            $4,
            $5,
            $6,
            $7,
            $8,
            $9,
            $10
        )
        RETURNING *;
        """

    transition_id = uuid7()
    await pool.fetchrow(
        create_execution_transition_query,
        str(execution_id),
        str(transition_id),
        type,
        "label",
        current_step,
        next_step,
        output,
        None,
        metadata,
        created_at,
    )


async def test_query_list_execution_inputs_data_search_window(
    pg_dsn,
    test_developer_id,
    custom_scope_id,
    test_task,
):
    pool = await create_db_pool(dsn=pg_dsn)
    scope_id = custom_scope_id

    execution_id = await create_execution(
        pool, test_developer_id, test_task.id, utcnow() - timedelta(weeks=1)
    )

    await create_transition(
        pool,
        execution_id,
        "init",
        {"workflow_name": "main", "step_index": 0, "scope_id": scope_id},
        {"workflow_name": "main", "step_index": 0, "scope_id": scope_id},
        {"init_step": "init step"},
        {},
        utcnow() - timedelta(weeks=1),
    )

    await create_transition(
        pool,
        execution_id,
        "step",
        {"workflow_name": "main", "step_index": 0, "scope_id": scope_id},
        {"workflow_name": "main", "step_index": 1, "scope_id": scope_id},
        {"step_step": "step step"},
        {},
        utcnow() - timedelta(days=1),
    )

    transitions_with_search_window = await list_execution_inputs_data(
        execution_id=execution_id,
        scope_id=scope_id,
        direction="asc",
        connection_pool=pool,
        search_window=timedelta(days=5),
    )

    assert len(transitions_with_search_window) == 1
    assert transitions_with_search_window[0].output == {"step_step": "step step"}

    transitions_without_search_window = await list_execution_inputs_data(
        execution_id=execution_id,
        scope_id=scope_id,
        direction="asc",
        connection_pool=pool,
    )

    assert len(transitions_without_search_window) == 2
    assert transitions_without_search_window[0].output == {"init_step": "init step"}
    assert transitions_without_search_window[1].output == {"step_step": "step step"}


async def test_query_list_execution_state_data_search_window(
    pg_dsn,
    test_developer_id,
    custom_scope_id,
    test_task,
):
    pool = await create_db_pool(dsn=pg_dsn)
    scope_id = custom_scope_id

    execution_id = await create_execution(
        pool, test_developer_id, test_task.id, utcnow() - timedelta(weeks=1)
    )

    await create_transition(
        pool,
        execution_id,
        "init",
        {"workflow_name": "main", "step_index": 0, "scope_id": scope_id},
        {"workflow_name": "main", "step_index": 0, "scope_id": scope_id},
        {"init_step": "init step"},
        {},
        utcnow() - timedelta(weeks=1),
    )

    await create_transition(
        pool,
        execution_id,
        "step",
        {"workflow_name": "main", "step_index": 0, "scope_id": scope_id},
        {"workflow_name": "main", "step_index": 1, "scope_id": scope_id},
        {"init_step": "init step"},
        {"step_type": "SetStep"},
        utcnow() - timedelta(weeks=1),
    )

    await create_transition(
        pool,
        execution_id,
        "step",
        {"workflow_name": "main", "step_index": 1, "scope_id": scope_id},
        {"workflow_name": "main", "step_index": 2, "scope_id": scope_id},
        {"step_step": "step step"},
        {"step_type": "SetStep"},
        utcnow() - timedelta(days=1),
    )

    transitions_with_search_window = await list_execution_state_data(
        execution_id=execution_id,
        scope_id=scope_id,
        direction="asc",
        connection_pool=pool,
        search_window=timedelta(days=5),
    )

    assert len(transitions_with_search_window) == 1
    assert transitions_with_search_window[0].output == {"step_step": "step step"}

    transitions_without_search_window = await list_execution_state_data(
        execution_id=execution_id,
        scope_id=scope_id,
        direction="asc",
        connection_pool=pool,
    )

    assert len(transitions_without_search_window) == 2
    assert transitions_without_search_window[0].output == {"init_step": "init step"}
    assert transitions_without_search_window[1].output == {"step_step": "step step"}

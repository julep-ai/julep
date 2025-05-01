import logging
from typing import Annotated
from uuid import UUID

from beartype import beartype
from fastapi import BackgroundTasks, Depends, HTTPException, status
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from starlette.status import HTTP_201_CREATED
from temporalio.client import WorkflowHandle
from uuid_extensions import uuid7

from ...autogen.openapi_model import (
    CreateExecutionRequest,
    CreateTransitionRequest,
    Execution,
    TransitionTarget,
)
from ...clients.temporal import run_task_execution_workflow
from ...common.protocol.developers import Developer
from ...common.protocol.models import task_to_spec
from ...dependencies.developer_id import get_developer_id
from ...env import max_free_executions, max_free_transitions
from ...queries.developers.get_developer import get_developer
from ...queries.executions.count_executions import (
    count_executions as count_executions_query,
)
from ...queries.executions.count_transitions import (
    count_transitions as count_transitions_query,
)
from ...queries.executions.create_execution import (
    create_execution as create_execution_query,
)
from ...queries.executions.create_execution_transition import (
    create_execution_transition,
)
from ...queries.executions.create_temporal_lookup import create_temporal_lookup
from ...queries.executions.prepare_execution_input import prepare_execution_input
from ...queries.tasks.get_task import get_task as get_task_query
from .router import router

logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@beartype
async def start_execution(
    *,
    developer_id: UUID,
    task_id: UUID,
    data: CreateExecutionRequest,
    connection_pool=None,
) -> tuple[Execution, WorkflowHandle]:
    execution_id = uuid7()

    execution = await create_execution_query(
        developer_id=developer_id,
        task_id=task_id,
        execution_id=execution_id,
        data=data,
        connection_pool=connection_pool,
    )

    execution_input = await prepare_execution_input(
        developer_id=developer_id,
        task_id=task_id,
        execution_id=execution_id,
        connection_pool=connection_pool,
    )

    task = await get_task_query(
        developer_id=developer_id,
        task_id=task_id,
        connection_pool=connection_pool,
    )

    execution_input.task = task_to_spec(task)
    execution_input.task.id = task.id

    job_id = uuid7()

    try:
        handle = await run_task_execution_workflow(
            execution_input=execution_input,
            job_id=job_id,
        )

    except Exception as e:
        logger.exception(e)

        await create_execution_transition(
            developer_id=developer_id,
            execution_id=execution_id,
            data=CreateTransitionRequest(
                type="error",
                output={"error": str(e)},
                current=TransitionTarget(
                    workflow="main",
                    step=0,
                    scope_id=uuid7(),
                ),
                next=None,
            ),
            connection_pool=connection_pool,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Execution creation failed",
        ) from e

    return execution, handle


@router.post(
    "/tasks/{task_id}/executions",
    status_code=HTTP_201_CREATED,
    tags=["executions"],
)
async def create_task_execution(
    task_id: UUID,
    data: CreateExecutionRequest,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    background_tasks: BackgroundTasks,
) -> Execution:
    try:
        task = await get_task_query(task_id=task_id, developer_id=x_developer_id)
        validate(data.input, task.input_schema)

    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request arguments schema",
        )

    # get developer data
    developer: Developer = await get_developer(developer_id=x_developer_id)

    # check if the developer is paid
    if "paid" not in developer.tags:
        # Check execution count
        executions = await count_executions_query(developer_id=x_developer_id, task_id=task_id)
        execution_count = executions["count"]
        if execution_count > max_free_executions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Execution count exceeded the free tier limit",
            )

        # Check transitions count
        transitions = await count_transitions_query(developer_id=x_developer_id)
        transition_count = transitions["count"]
        if transition_count > max_free_transitions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Transition count exceeded the free tier limit",
            )

    execution, handle = await start_execution(
        developer_id=x_developer_id,
        task_id=task_id,
        data=data,
    )

    background_tasks.add_task(
        create_temporal_lookup,
        execution_id=execution.id,
        workflow_handle=handle,
    )

    execution.metadata = {"jobs": [handle.id]}
    return execution

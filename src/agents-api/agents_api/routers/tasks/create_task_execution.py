# AIDEV-NOTE: This module defines the API endpoint for creating and initiating task executions.
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
from ...env import max_free_executions
from ...queries.developers.get_developer import get_developer
from ...queries.executions.count_executions import (
    count_executions as count_executions_query,
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


# AIDEV-NOTE: Initiates a task execution by creating a database entry and starting the Temporal workflow.
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
        # AIDEV-NOTE: Runs the Temporal task execution workflow.
        handle = await run_task_execution_workflow(
            execution_input=execution_input,
            job_id=job_id,
        )

    except Exception as e:
        logger.exception(e)

        # AIDEV-NOTE: Creates an error transition in the database if the workflow fails to start.
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


# AIDEV-NOTE: API endpoint to create a new task execution for a given task.
# It depends on developer ID, task ID from the path, and execution data from the request body.
# Includes validation for the input data schema and checks for free tier limits before starting the execution.
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
        # AIDEV-NOTE: Validates the input data against the task's input schema.
        task = await get_task_query(task_id=task_id, developer_id=x_developer_id)
        validate(data.input, task.input_schema)

    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request arguments schema",
        )

    # AIDEV-NOTE: Checks if the developer is within the free tier execution limit for the task.
    # get developer data
    developer: Developer = await get_developer(developer_id=x_developer_id)

    # check if the developer is paid
    if "paid" not in developer.tags:
        executions = await count_executions_query(developer_id=x_developer_id, task_id=task_id)

        execution_count = executions["count"]
        if execution_count > max_free_executions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Execution count exceeded the free tier limit",
            )

    # AIDEV-NOTE: Starts the task execution and creates a Temporal lookup entry in the background.
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

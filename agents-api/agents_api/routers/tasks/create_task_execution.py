import logging
from typing import Annotated
from uuid import UUID, uuid4

from beartype import beartype
from fastapi import BackgroundTasks, Depends, HTTPException, status
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from pycozo.client import QueryException
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED
from temporalio.client import WorkflowHandle

from ...autogen.Executions import Execution
from ...autogen.openapi_model import (
    CreateExecutionRequest,
    ResourceCreatedResponse,
    UpdateExecutionRequest,
)
from ...clients.temporal import run_task_execution_workflow
from ...dependencies.developer_id import get_developer_id
from ...models.execution.create_execution import (
    create_execution as create_execution_query,
)
from ...models.execution.create_temporal_lookup import create_temporal_lookup
from ...models.execution.prepare_execution_input import prepare_execution_input
from ...models.execution.update_execution import (
    update_execution as update_execution_query,
)
from ...models.task.get_task import get_task as get_task_query
from .router import router

logger: logging.Logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@beartype
async def start_execution(
    *,
    developer_id: UUID,
    task_id: UUID,
    data: CreateExecutionRequest,
    client=None,
) -> tuple[Execution, WorkflowHandle]:
    execution_id = uuid4()

    execution = create_execution_query(
        developer_id=developer_id,
        task_id=task_id,
        execution_id=execution_id,
        data=data,
        client=client,
    )

    execution_input = prepare_execution_input(
        developer_id=developer_id,
        task_id=task_id,
        execution_id=execution_id,
        client=client,
    )

    job_id = uuid4()

    try:
        handle = await run_task_execution_workflow(
            execution_input=execution_input,
            job_id=job_id,
        )

    except Exception as e:
        logger.exception(e)

        update_execution_query(
            developer_id=developer_id,
            task_id=task_id,
            execution_id=execution_id,
            data=UpdateExecutionRequest(status="failed"),
            client=client,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Execution creation failed",
        ) from e

    return execution, handle


@router.post(
    "/tasks/{task_id}/executions",
    status_code=HTTP_201_CREATED,
    tags=["tasks"],
)
async def create_task_execution(
    task_id: UUID4,
    data: CreateExecutionRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    background_tasks: BackgroundTasks,
) -> ResourceCreatedResponse:
    try:
        task = get_task_query(task_id=task_id, developer_id=x_developer_id)
        validate(data.input, task.input_schema)

    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request arguments schema",
        )
    except QueryException as e:
        if e.code == "transact::assertion_failure":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        raise

    execution, handle = await start_execution(
        developer_id=x_developer_id,
        task_id=task_id,
        data=data,
    )

    background_tasks.add_task(
        create_temporal_lookup,
        #
        developer_id=x_developer_id,
        execution_id=execution.id,
        workflow_handle=handle,
    )

    return ResourceCreatedResponse(
        id=execution.id,
        created_at=execution.created_at,
        jobs=[handle.id],
    )

import logging
from typing import Annotated
from uuid import UUID

from beartype import beartype
from fastapi import BackgroundTasks, Depends, HTTPException, status
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from pycozo.client import QueryException
from starlette.status import HTTP_201_CREATED
from temporalio.client import WorkflowHandle
from uuid_extensions import uuid7

from ...autogen.openapi_model import (
    CreateExecutionRequest,
    Execution,
    ResourceCreatedResponse,
    UpdateExecutionRequest,
)
from ...clients.temporal import run_task_execution_workflow
from ...common.protocol.developers import Developer
from ...dependencies.developer_id import get_developer_id
from ...env import max_free_executions
from ...queries.developers.get_developer import get_developer
from ...queries.executions.count_executions import (
    count_executions as count_executions_query,
)
from ...queries.executions.create_execution import (
    create_execution as create_execution_query,
)
from ...queries.executions.create_temporal_lookup import create_temporal_lookup
from ...queries.executions.prepare_execution_input import prepare_execution_input
from ...queries.executions.update_execution import (
    update_execution as update_execution_query,
)
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
    client=None,
) -> tuple[Execution, WorkflowHandle]:
    execution_id = uuid7()

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

    job_id = uuid7()

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
    tags=["executions"],
)
async def create_task_execution(
    task_id: UUID,
    data: CreateExecutionRequest,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
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

    # get developer data
    developer: Developer = get_developer(developer_id=x_developer_id)

    # # check if the developer is paid
    if "paid" not in developer.tags:
        executions = count_executions_query(
            developer_id=x_developer_id, task_id=task_id
        )

        execution_count = executions["count"]
        if execution_count > max_free_executions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Execution count exceeded the free tier limit",
            )

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

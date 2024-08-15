import logging
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from pycozo.client import QueryException
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED

from agents_api.autogen.openapi_model import (
    CreateExecutionRequest,
    ResourceCreatedResponse,
    UpdateExecutionRequest,
)
from agents_api.clients.temporal import run_task_execution_workflow
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.execution.create_execution import (
    create_execution as create_execution_query,
)
from agents_api.models.execution.prepare_execution_input import prepare_execution_input
from agents_api.models.execution.update_execution import (
    update_execution as update_execution_query,
)
from agents_api.models.task.get_task import get_task as get_task_query

from .router import router

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@router.post(
    "/tasks/{task_id}/executions",
    status_code=HTTP_201_CREATED,
    tags=["tasks"],
)
async def create_task_execution(
    task_id: UUID4,
    data: CreateExecutionRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    try:
        task = get_task_query(
            task_id=task_id, developer_id=x_developer_id
        )
        task_data = task.model_dump()

        validate(data.input, task_data["input_schema"])
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

    execution_id = uuid4()
    execution_input = prepare_execution_input(
        developer_id=x_developer_id,
        task_id=task_id,
        execution_id=execution_id,
    )

    try:
        handle = await run_task_execution_workflow(
            execution_input=execution_input,
            job_id=uuid4(),
        )
    except Exception as e:
        logger.exception(e)

        update_execution_query(
            developer_id=x_developer_id,
            task_id=task_id,
            execution_id=execution_id,
            data=UpdateExecutionRequest(status="failed"),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Task creation failed",
        )

    execution = create_execution_query(
        developer_id=x_developer_id,
        task_id=task_id,
        execution_id=execution_id,
        data=data,
        workflow_hande=handle,
    )

    return ResourceCreatedResponse(
        id=execution["execution_id"][0], created_at=execution["created_at"][0]
    )

from typing import Annotated

from fastapi import Depends, HTTPException, status
from pydantic import UUID4

from agents_api.autogen.openapi_model import (
    Execution,
    ResourceUpdatedResponse,
    UpdateExecutionRequest,
)
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.execution.update_execution import (
    update_execution as update_execution_query,
)

from .router import router


# TODO: write PATCH query
@router.patch("/tasks/{task_id}/executions/{execution_id}", tags=["tasks"])
async def patch_execution(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    task_id: UUID4,
    execution_id: UUID4,
    data: UpdateExecutionRequest,
) -> ResourceUpdatedResponse:
    return update_execution_query(
        developer_id=x_developer_id,
        task_id=task_id,
        execution_id=execution_id,
        data=data,
    )

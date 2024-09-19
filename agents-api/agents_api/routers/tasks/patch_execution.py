from typing import Annotated

from fastapi import Depends
from uuid import UUID

from agents_api.autogen.openapi_model import (
    ResourceUpdatedResponse,
    UpdateExecutionRequest,
)
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.execution.update_execution import (
    update_execution as update_execution_query,
)

from .router import router


@router.patch("/tasks/{task_id}/executions/{execution_id}", tags=["tasks"])
async def patch_execution(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    task_id: UUID,
    execution_id: UUID,
    data: UpdateExecutionRequest,
) -> ResourceUpdatedResponse:
    return update_execution_query(
        developer_id=x_developer_id,
        task_id=task_id,
        execution_id=execution_id,
        data=data,
    )

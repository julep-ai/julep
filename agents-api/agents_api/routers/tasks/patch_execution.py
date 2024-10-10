from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import (
    ResourceUpdatedResponse,
    UpdateExecutionRequest,
)
from ...dependencies.developer_id import get_developer_id
from ...models.execution.update_execution import (
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

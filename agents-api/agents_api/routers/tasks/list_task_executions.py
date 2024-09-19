from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends

from agents_api.autogen.openapi_model import (
    Execution,
    ListResponse,
)
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.execution.list_executions import (
    list_executions as list_task_executions_query,
)

from .router import router


@router.get("/tasks/{task_id}/executions", tags=["tasks"])
async def list_task_executions(
    task_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> ListResponse[Execution]:
    executions = list_task_executions_query(
        task_id=task_id,
        developer_id=x_developer_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
    )
    return ListResponse[Execution](items=executions)

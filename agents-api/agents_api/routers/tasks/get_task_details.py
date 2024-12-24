from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import (
    Task,
)
from ...dependencies.developer_id import get_developer_id
from ...queries.tasks.get_task import get_task as get_task_query
from .router import router


@router.get("/tasks/{task_id}", tags=["tasks"])
async def get_task_details(
    task_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> Task:
    task = await get_task_query(developer_id=x_developer_id, task_id=task_id)
    task_data = task.model_dump()

    for workflow in task_data.get("workflows", []):
        if workflow["name"] == "main":
            task_data["main"] = workflow.get("steps", [])
            break

    return Task(**task_data)

from typing import Annotated, Literal

from fastapi import Depends
from pydantic import UUID4

from agents_api.autogen.openapi_model import (
    ListResponse,
    Task,
)
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.task.list_tasks import list_tasks as list_tasks_query

from .router import router


@router.get("/agents/{agent_id}/tasks", tags=["tasks"])
async def list_tasks(
    agent_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> ListResponse[Task]:
    query_results = list_tasks_query(
        agent_id=agent_id,
        developer_id=x_developer_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
    )

    tasks = []
    for row in query_results:
        row_dict = row.model_dump()

        for workflow in row_dict.get("workflows", []):
            if workflow["name"] == "main":
                row_dict["main"] = workflow["steps"]
                break

        tasks.append(Task(**row_dict))

    return ListResponse[Task](items=tasks)

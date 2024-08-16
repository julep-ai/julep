from typing import Annotated

from fastapi import Depends, HTTPException, status
from pycozo.client import QueryException
from pydantic import UUID4

from agents_api.autogen.openapi_model import (
    Task,
)
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.task.get_task import get_task as get_task_query

from .router import router


@router.get("/tasks/{task_id}", tags=["tasks"])
async def get_task_details(
    task_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> Task:
    not_found = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
    )

    try:
        task = get_task_query(developer_id=x_developer_id, task_id=task_id)
        task_data = task.model_dump()
    except AssertionError:
        raise not_found
    except QueryException as e:
        if e.code == "transact::assertion_failure":
            raise not_found

        raise

    for workflow in task_data.get("workflows", []):
        if workflow["name"] == "main":
            task_data["main"] = workflow.get("steps", [])
            break

    return Task(**task_data)

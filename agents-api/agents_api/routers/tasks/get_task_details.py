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


@router.get("/agents/{agent_id}/tasks/{task_id}", tags=["tasks"])
async def get_task_details(
    task_id: UUID4,
    agent_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> Task:
    try:
        resp = [
            row.to_dict()
            for _, row in get_task_query(
                agent_id=agent_id, task_id=task_id, developer_id=x_developer_id
            ).iterrows()
        ][0]

        for workflow in resp["workflows"]:
            if workflow["name"] == "main":
                resp["main"] = workflow["steps"]
                break

        return Task(**resp)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    except QueryException as e:
        if e.code == "transact::assertion_failure":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )

        raise

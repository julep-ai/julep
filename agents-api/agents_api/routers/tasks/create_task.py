from typing import Annotated
from uuid import uuid4

import pandas as pd
from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED

from agents_api.autogen.openapi_model import (
    CreateTaskRequest,
    ResourceCreatedResponse,
)
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.task.create_task import create_task as create_task_query

from .router import router


@router.post("/agents/{agent_id}/tasks", status_code=HTTP_201_CREATED, tags=["tasks"])
async def create_task(
    request: CreateTaskRequest,
    agent_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    task_id = uuid4()

    # TODO: Do thorough validation of the task spec

    workflows = [
        {"name": "main", "steps": [w.model_dump() for w in request.main]},
    ] + [{"name": name, "steps": steps} for name, steps in request.model_extra.items()]

    resp: pd.DataFrame = create_task_query(
        agent_id=agent_id,
        task_id=task_id,
        developer_id=x_developer_id,
        name=request.name,
        description=request.description,
        input_schema=request.input_schema or {},
        tools_available=request.tools or [],
        workflows=workflows,
    )

    return ResourceCreatedResponse(
        id=resp["task_id"][0], created_at=resp["created_at"][0]
    )

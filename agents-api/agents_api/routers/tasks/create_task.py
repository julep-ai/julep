from typing import Annotated

from fastapi import Depends, HTTPException
from jsonschema import validate
from jsonschema.exceptions import SchemaError, ValidationError
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
    data: CreateTaskRequest,
    agent_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    # TODO: Do thorough validation of the task spec

    # Validate the input schema
    try:
        if data.input_schema is not None:
            validate(None, data.input_schema)

    except SchemaError:
        raise HTTPException(detail="Invalid input schema", status_code=400)

    except ValidationError:
        pass

    task = create_task_query(
        developer_id=x_developer_id,
        agent_id=agent_id,
        data=data,
    )

    return ResourceCreatedResponse(id=task.id, created_at=task.created_at, jobs=[])

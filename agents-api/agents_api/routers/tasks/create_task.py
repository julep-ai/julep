from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from jsonschema import validate
from jsonschema.exceptions import SchemaError, ValidationError
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    CreateTaskRequest,
    ResourceCreatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from ...models.task.create_task import create_task as create_task_query
from .router import router


@router.post("/agents/{agent_id}/tasks", status_code=HTTP_201_CREATED, tags=["tasks"])
async def create_task(
    data: CreateTaskRequest,
    agent_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    # TODO: Do thorough validation of the task spec
    # SCRUM-10

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

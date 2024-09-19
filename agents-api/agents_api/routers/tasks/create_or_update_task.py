from typing import Annotated

from fastapi import Depends, HTTPException
from jsonschema import validate
from jsonschema.exceptions import SchemaError, ValidationError
from uuid import UUID
from starlette.status import HTTP_201_CREATED

from agents_api.autogen.openapi_model import (
    CreateOrUpdateTaskRequest,
    ResourceUpdatedResponse,
)
from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.task.create_or_update_task import (
    create_or_update_task as create_or_update_task_query,
)

from .router import router


@router.post(
    "/agents/{agent_id}/tasks/{task_id}", status_code=HTTP_201_CREATED, tags=["tasks"]
)
async def create_or_update_task(
    data: CreateOrUpdateTaskRequest,
    agent_id: UUID,
    task_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ResourceUpdatedResponse:
    # TODO: Do thorough validation of the task spec
    # SCRUM-10

    # FIXME: There is also some subtle bug here that prevents us from
    #        starting executions from tasks created via this endpoint
    # SCRUM-9

    # Validate the input schema
    try:
        if data.input_schema is not None:
            validate(None, data.input_schema)

    except SchemaError:
        raise HTTPException(detail="Invalid input schema", status_code=400)

    except ValidationError:
        pass

    task = create_or_update_task_query(
        developer_id=x_developer_id,
        agent_id=agent_id,
        task_id=task_id,
        data=data,
    )

    return ResourceUpdatedResponse(id=task.id, updated_at=task.updated_at, jobs=[])

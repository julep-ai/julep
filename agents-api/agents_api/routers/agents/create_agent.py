from typing import Annotated
from uuid import uuid4

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    CreateAgentRequest,
    ResourceCreatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from ...models.agent.create_agent import create_agent as create_agent_query
from .router import router


@router.post("/agents", status_code=HTTP_201_CREATED, tags=["agents"])
async def create_agent(
    request: CreateAgentRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    new_agent_id = uuid4()

    _, resp = next(
        create_agent_query(
            developer_id=x_developer_id,
            agent_id=new_agent_id,
            name=request.name,
            about=request.about,
            instructions=request.instructions or [],
            model=request.model,
            default_settings=request.default_settings or {},
            metadata=request.metadata or {},
        ).iterrows()
    )

    return ResourceCreatedResponse(id=new_agent_id, created_at=resp["created_at"])

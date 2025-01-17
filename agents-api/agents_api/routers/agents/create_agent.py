from typing import Annotated
from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    CreateAgentRequest,
    ResourceCreatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from ...queries.agents.create_agent import CreateAgentQuery
from ...queries.container import Queries
from .router import router


@router.post("/agents", status_code=HTTP_201_CREATED, tags=["agents"])
@inject
async def create_agent(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    data: CreateAgentRequest,
    query: CreateAgentQuery = Depends(Provide[Queries.agents.create])
) -> ResourceCreatedResponse:
    agent = await query.execute(
        developer_id=x_developer_id,
        data=data,
    )

    return ResourceCreatedResponse(id=agent.id, created_at=agent.created_at, jobs=[])

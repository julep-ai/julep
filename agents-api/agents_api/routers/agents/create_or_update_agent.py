from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED

import agents_api.models as models

from ...autogen.openapi_model import (
    CreateOrUpdateAgentRequest,
    ResourceCreatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from .router import router


@router.post("/agents/{agent_id}", status_code=HTTP_201_CREATED, tags=["agents"])
async def create_or_update_agent(
    agent_id: UUID,
    data: CreateOrUpdateAgentRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    # TODO: Validate model name
    agent = models.agent.create_or_update_agent(
        developer_id=x_developer_id,
        agent_id=agent_id,
        data=data,
    )

    return ResourceCreatedResponse(id=agent.id, created_at=agent.created_at, jobs=[])

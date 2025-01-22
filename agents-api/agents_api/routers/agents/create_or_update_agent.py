from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    CreateOrUpdateAgentRequest,
    ResourceCreatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from ...queries.agents.create_or_update_agent import (
    create_or_update_agent as create_or_update_agent_query,
)
from ..utils.model_validation import validate_model
from .router import router


@router.post("/agents/{agent_id}", status_code=HTTP_201_CREATED, tags=["agents"])
async def create_or_update_agent(
    agent_id: UUID,
    data: CreateOrUpdateAgentRequest,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    if data.model:
        await validate_model(data.model)

    agent = await create_or_update_agent_query(
        developer_id=x_developer_id,
        agent_id=agent_id,
        data=data,
    )

    return ResourceCreatedResponse(id=agent.id, created_at=agent.created_at, jobs=[])

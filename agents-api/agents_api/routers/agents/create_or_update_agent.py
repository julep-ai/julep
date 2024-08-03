from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    CreateOrUpdateAgentRequest,
    ResourceCreatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from ...models.agent.create_or_update_agent import (
    create_or_update_agent as create_or_update_agent_query,
)
from .router import router


@router.post("/agents/{agent_id}", status_code=HTTP_201_CREATED, tags=["agents"])
async def create_or_update_agent(
    agent_id: UUID,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    data: CreateOrUpdateAgentRequest,
) -> ResourceCreatedResponse:
    _, resp = next(
        create_or_update_agent_query(
            developer_id=x_developer_id,
            agent_id=agent_id,
            data=data,
        ).iterrows()
    )

    return ResourceCreatedResponse(id=agent_id, created_at=resp["created_at"])

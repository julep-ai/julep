from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED

import agents_api.models as models

from ...autogen.openapi_model import (
    CreateToolRequest,
    ResourceCreatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from .router import router


@router.post("/agents/{agent_id}/tools", status_code=HTTP_201_CREATED, tags=["agents"])
async def create_agent_tool(
    agent_id: UUID,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    data: CreateToolRequest,
) -> ResourceCreatedResponse:
    tool = models.tools.create_tools(
        developer_id=x_developer_id,
        agent_id=agent_id,
        data=[data],
    )[0]

    return ResourceCreatedResponse(id=tool.id, created_at=tool.created_at, jobs=[])

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_201_CREATED

from ...queries.tools.create_tools import create_tools as create_tools_query

from ...autogen.openapi_model import (
    CreateToolRequest,
    ResourceCreatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from ...queries.tools.create_tools import create_tools as create_tools_query
from .router import router


@router.post("/agents/{agent_id}/tools", status_code=HTTP_201_CREATED, tags=["agents"])
async def create_agent_tool(
    agent_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    data: CreateToolRequest,
) -> ResourceCreatedResponse:
    tool = await create_tools_query(
        developer_id=x_developer_id,
        agent_id=agent_id,
        data=[data],
    )[0]

    return ResourceCreatedResponse(id=tool.id, created_at=tool.created_at, jobs=[])

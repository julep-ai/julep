from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    CreateAgentRequest,
    CreateOrUpdateAgentRequest,
    CreateToolRequest,
    ResourceCreatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from ...models.tools.create_tools import create_tools as create_tools_query
from .router import router


@router.post("/agents/{agent_id}/tools", status_code=HTTP_201_CREATED, tags=["agents"])
async def create_agent_tools(
    agent_id: UUID,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    data: list[CreateToolRequest],
    ignore_existing: bool = False,
) -> ResourceCreatedResponse:
    _, resp = next(
        create_tools_query(
            developer_id=x_developer_id,
            agent_id=agent_id,
            data=data,
            ignore_existing=ignore_existing,
        ).iterrows()
    )

    return ResourceCreatedResponse(id=resp["tool_id"], created_at=resp["created_at"])

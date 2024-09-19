from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends
from uuid import UUID

from ...autogen.openapi_model import ListResponse, Tool
from ...dependencies.developer_id import get_developer_id
from ...models.tools.list_tools import list_tools as list_tools_query
from .router import router


@router.get("/agents/{agent_id}/tools", tags=["agents"])
async def list_agent_tools(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    agent_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> ListResponse[Tool]:
    # FIXME: list agent tools is returning an empty list
    # SCRUM-22
    tools = list_tools_query(
        agent_id=agent_id,
        developer_id=x_developer_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
    )

    return ListResponse[Tool](items=tools)

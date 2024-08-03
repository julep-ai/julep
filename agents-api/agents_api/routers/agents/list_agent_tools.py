from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends
from pydantic import UUID4

from ...dependencies.developer_id import get_developer_id
from ...models.tools.list_tools import list_tools as list_tools_query
from .router import router


@router.get("/agents/{agent_id}/tools", tags=["agents"])
async def list_agent_tools(
    agent_id: UUID,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> list[tuple[str, dict]]:
    return [
        row
        for _, row in list_tools_query(
            developer_id=x_developer_id,
            agent_id=agent_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            direction=direction,
        ).iterrows()
    ]

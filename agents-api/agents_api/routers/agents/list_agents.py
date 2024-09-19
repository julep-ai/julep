import json
from json import JSONDecodeError
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from uuid import UUID

from ...autogen.openapi_model import Agent, ListResponse
from ...dependencies.developer_id import get_developer_id
from ...models.agent.list_agents import list_agents as list_agents_query
from .router import router


@router.get("/agents", tags=["agents"])
async def list_agents(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: str = "{}",
) -> ListResponse[Agent]:
    try:
        metadata_filter = json.loads(metadata_filter)
    except JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="metadata_filter is not a valid JSON",
        )

    agents = list_agents_query(
        developer_id=x_developer_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter,
    )

    return ListResponse[Agent](items=agents)

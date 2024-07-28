from typing import Annotated, List

from fastapi import Depends
from pydantic import UUID4

from ...autogen.openapi_model import Agent
from ...dependencies.developer_id import get_developer_id
from ...models.agent.list_agents import list_agents_query
from .router import router


@router.get("/agents", tags=["agents"])
async def list_agents(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
    metadata_filter: str = "{}",
) -> List[Agent]:
    agents = list_agents_query(
        developer_id=x_developer_id,
        limit=limit,
        offset=offset,
        metadata_filter=metadata_filter,
    )
    return [Agent(**agent) for agent in agents]

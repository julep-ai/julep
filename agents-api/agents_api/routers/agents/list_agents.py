from fastapi import APIRouter, Depends
from pydantic import UUID4
from typing import List

from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.agent.list_agents import list_agents_query
from agents_api.autogen.openapi_model import Agent

router = APIRouter()

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

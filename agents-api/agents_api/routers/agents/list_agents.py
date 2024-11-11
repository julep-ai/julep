from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import Agent, ListResponse
from ...dependencies.developer_id import get_developer_id
from ...dependencies.query_filter import MetadataFilter, create_filter_extractor
from ...models.agent.list_agents import list_agents as list_agents_query
from .router import router


@router.get("/agents", tags=["agents"])
async def list_agents(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    # Expects the dot notation of object in query params
    # Example:
    # > ?metadata_filter.name=John&metadata_filter.age=30
    metadata_filter: Annotated[
        MetadataFilter, Depends(create_filter_extractor("metadata_filter"))
    ],
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> ListResponse[Agent]:
    agents = list_agents_query(
        developer_id=x_developer_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter.model_dump(mode="json") or {},
    )

    return ListResponse[Agent](items=agents)

# AIDEV-NOTE: This module defines the API endpoint for listing sessions with filtering, pagination, and sorting.
from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import ListResponse, Session
from ...dependencies.developer_id import get_developer_id
from ...dependencies.query_filter import MetadataFilter, create_filter_extractor
from ...queries.sessions.list_sessions import list_sessions as list_sessions_query
from .router import router


# AIDEV-NOTE: API endpoint to list sessions.
# Supports filtering by metadata, pagination (limit, offset), and sorting (sort_by, direction).
# It depends on developer ID, metadata filter, and query parameters, and calls the list_sessions_query function.
@router.get("/sessions", tags=["sessions"])
async def list_sessions(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    metadata_filter: Annotated[
        MetadataFilter,
        Depends(create_filter_extractor("metadata_filter")),
    ] = MetadataFilter(),
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> ListResponse[Session]:
    sessions = await list_sessions_query(
        developer_id=x_developer_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter.model_dump(mode="json") or {},
    )

    return ListResponse[Session](items=sessions)

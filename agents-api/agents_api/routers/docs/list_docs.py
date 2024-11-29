from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import Doc, ListResponse
from ...dependencies.developer_id import get_developer_id
from ...dependencies.query_filter import MetadataFilter, create_filter_extractor
from ...models.docs.list_docs import list_docs as list_docs_query
from .router import router


@router.get("/users/{user_id}/docs", tags=["docs"])
async def list_user_docs(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    user_id: UUID,
    metadata_filter: Annotated[
        MetadataFilter,
        Depends(create_filter_extractor("metadata_filter")),
    ],
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> ListResponse[Doc]:
    docs = list_docs_query(
        developer_id=x_developer_id,
        owner_type="user",
        owner_id=user_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter.model_dump(mode="json"),
    )

    return ListResponse[Doc](items=docs)


@router.get("/agents/{agent_id}/docs", tags=["docs"])
async def list_agent_docs(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    agent_id: UUID,
    metadata_filter: Annotated[
        MetadataFilter, Depends(create_filter_extractor("metadata_filter"))
    ],
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> ListResponse[Doc]:
    docs = list_docs_query(
        developer_id=x_developer_id,
        owner_type="agent",
        owner_id=agent_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter.model_dump(mode="json"),
    )

    return ListResponse[Doc](items=docs)

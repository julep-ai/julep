import json
from json import JSONDecodeError
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from pydantic import UUID4

from ...autogen.openapi_model import Doc, ListResponse
from ...dependencies.developer_id import get_developer_id
from ...models.docs.list_docs import list_docs as list_docs_query
from .router import router


@router.get("/users/{user_id}/docs", tags=["docs"])
async def list_user_docs(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    user_id: UUID4,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: str = "{}",
) -> ListResponse[Doc]:
    try:
        metadata_filter = json.loads(metadata_filter)
    except JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="metadata_filter is not a valid JSON",
        )

    docs = list_docs_query(
        developer_id=x_developer_id,
        owner_type="user",
        owner_id=user_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter,
    )

    return ListResponse[Doc](items=docs)


@router.get("/agents/{agent_id}/docs", tags=["docs"])
async def list_agent_docs(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    agent_id: UUID4,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: str = "{}",
) -> ListResponse[Doc]:
    try:
        metadata_filter = json.loads(metadata_filter)
    except JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="metadata_filter is not a valid JSON",
        )

    docs = list_docs_query(
        developer_id=x_developer_id,
        owner_type="agent",
        owner_id=agent_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter,
    )

    return ListResponse[Doc](items=docs)

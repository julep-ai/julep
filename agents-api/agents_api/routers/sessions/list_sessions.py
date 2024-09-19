import json
from json import JSONDecodeError
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from uuid import UUID

from ...autogen.openapi_model import ListResponse, Session
from ...dependencies.developer_id import get_developer_id
from ...models.session.list_sessions import list_sessions as list_sessions_query
from .router import router


@router.get("/sessions", tags=["sessions"])
async def list_sessions(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: str = "{}",
) -> ListResponse[Session]:
    try:
        metadata_filter = json.loads(metadata_filter)
    except JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="metadata_filter is not a valid JSON",
        )

    sessions = list_sessions_query(
        developer_id=x_developer_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter,
    )

    return ListResponse[Session](items=sessions)

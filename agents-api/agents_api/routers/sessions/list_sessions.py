import json
from json import JSONDecodeError
from typing import Annotated

from fastapi import Depends, HTTPException, status
from pydantic import UUID4, BaseModel

from ...dependencies.developer_id import get_developer_id
from ...models.session.list_sessions import list_sessions_query
from ...autogen.openapi_model import Session

from .router import router


class SessionList(BaseModel):
    items: list[Session]


@router.get("/sessions", tags=["sessions"])
async def list_sessions(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
    metadata_filter: str = "{}",
) -> SessionList:
    try:
        metadata_filter = json.loads(metadata_filter)
    except JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="metadata_filter is not a valid JSON",
        )

    query_results = list_sessions_query(
        x_developer_id, limit, offset, metadata_filter=metadata_filter
    )

    return SessionList(
        items=[Session(**row.to_dict()) for _, row in query_results.iterrows()]
    )

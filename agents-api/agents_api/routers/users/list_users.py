import json
from json import JSONDecodeError
from typing import Annotated, Literal

from fastapi import Depends, HTTPException, status
from pydantic import UUID4

from ...autogen.openapi_model import ListResponse, User
from ...dependencies.developer_id import get_developer_id
from ...models.user.list_users import list_users as list_users_query
from .router import router


@router.get("/users", tags=["users"])
async def list_users(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: str = "{}",
) -> ListResponse[User]:
    try:
        metadata_filter = json.loads(metadata_filter)
    except JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="metadata_filter is not a valid JSON",
        )

    users = list_users_query(
        developer_id=x_developer_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter,
    )

    result = ListResponse[User](items=users)
    return result

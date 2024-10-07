from typing import Annotated, Literal
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import ListResponse, User
from ...dependencies.developer_id import get_developer_id
from ...dependencies.query_filter import create_filter_extractor
from ...models.user.list_users import list_users as list_users_query
from .router import router


@router.get("/users", tags=["users"])
async def list_users(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    metadata_filter: Annotated[
        dict, Depends(create_filter_extractor("metadata_filter"))
    ],
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> ListResponse[User]:
    users = list_users_query(
        developer_id=x_developer_id,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        direction=direction,
        metadata_filter=metadata_filter or {},
    )

    return ListResponse[User](items=users)

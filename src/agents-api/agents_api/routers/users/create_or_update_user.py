from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import CreateOrUpdateUserRequest, User
from ...dependencies.developer_id import get_developer_id
from ...queries.users.create_or_update_user import (
    create_or_update_user as create_or_update_user_query,
)
from .router import router


@router.post("/users/{user_id}", status_code=HTTP_201_CREATED, tags=["users"])
async def create_or_update_user(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    user_id: UUID,
    data: CreateOrUpdateUserRequest,
) -> User:
    return await create_or_update_user_query(
        developer_id=x_developer_id,
        user_id=user_id,
        data=data,
    )

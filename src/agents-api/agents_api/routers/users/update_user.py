from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import UpdateUserRequest, User
from ...dependencies.developer_id import get_developer_id
from ...queries.users.update_user import update_user as update_user_query
from .router import router


@router.put("/users/{user_id}", tags=["users"])
async def update_user(
    user_id: UUID,
    data: UpdateUserRequest,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> User:
    return await update_user_query(
        developer_id=x_developer_id,
        user_id=user_id,
        data=data,
    )

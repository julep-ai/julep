from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import User
from ...dependencies.developer_id import get_developer_id
from ...models.user.get_user import get_user as get_user_query
from .router import router


@router.get("/users/{user_id}", tags=["users"])
async def get_user_details(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    user_id: UUID,
) -> User:
    return get_user_query(developer_id=x_developer_id, user_id=user_id)

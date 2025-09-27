from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import CreateUserRequest, User
from ...dependencies.developer_id import get_developer_id
from ...queries.users.create_user import create_user as create_user_query
from .router import router


@router.post("/users", status_code=HTTP_201_CREATED, tags=["users"])
async def create_user(
    data: CreateUserRequest,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> User:
    return await create_user_query(
        developer_id=x_developer_id,
        data=data,
    )

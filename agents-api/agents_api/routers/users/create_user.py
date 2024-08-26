from typing import Annotated

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import CreateUserRequest, ResourceCreatedResponse
from ...dependencies.developer_id import get_developer_id
from ...models.user.create_user import create_user as create_user_query
from .router import router


@router.post("/users", status_code=HTTP_201_CREATED, tags=["users"])
async def create_user(
    data: CreateUserRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    user = create_user_query(
        developer_id=x_developer_id,
        data=data,
    )

    return ResourceCreatedResponse(id=user.id, created_at=user.created_at, jobs=[])

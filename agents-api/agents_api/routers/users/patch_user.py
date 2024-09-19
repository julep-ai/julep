from typing import Annotated

from fastapi import Depends
from uuid import UUID

from ...autogen.openapi_model import PatchUserRequest, ResourceUpdatedResponse
from ...dependencies.developer_id import get_developer_id
from ...models.user.patch_user import patch_user as patch_user_query
from .router import router


@router.patch("/users/{user_id}", tags=["users"])
async def patch_user(
    user_id: UUID,
    data: PatchUserRequest,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ResourceUpdatedResponse:
    return patch_user_query(
        developer_id=x_developer_id,
        user_id=user_id,
        data=data,
    )

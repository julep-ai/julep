from typing import Annotated

from fastapi import Depends
from uuid import UUID
from starlette.status import HTTP_202_ACCEPTED

from ...autogen.openapi_model import ResourceDeletedResponse
from ...dependencies.developer_id import get_developer_id
from ...models.user.delete_user import delete_user as delete_user_query
from .router import router


@router.delete("/users/{user_id}", status_code=HTTP_202_ACCEPTED, tags=["users"])
async def delete_user(
    user_id: UUID, x_developer_id: Annotated[UUID, Depends(get_developer_id)]
) -> ResourceDeletedResponse:
    return delete_user_query(developer_id=x_developer_id, user_id=user_id)

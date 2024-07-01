from typing import Annotated

from fastapi import HTTPException, Depends
from pydantic import UUID4
from starlette.status import HTTP_404_NOT_FOUND

from ...dependencies.developer_id import get_developer_id
from ...common.exceptions.users import UserNotFoundError
from ...models.user.patch_user import patch_user_query
from ...autogen.openapi_model import PatchUserRequest, ResourceUpdatedResponse

from .router import router


@router.patch("/users/{user_id}", tags=["users"])
async def patch_user(
    user_id: UUID4,
    request: PatchUserRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceUpdatedResponse:
    try:
        resp = patch_user_query(
            developer_id=x_developer_id,
            user_id=user_id,
            name=request.name,
            about=request.about,
            metadata=request.metadata,
        )

        return ResourceUpdatedResponse(
            id=resp["user_id"][0],
            updated_at=resp["updated_at"][0],
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except UserNotFoundError as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))

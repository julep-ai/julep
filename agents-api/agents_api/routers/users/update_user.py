from typing import Annotated

from fastapi import Depends, HTTPException
from pydantic import UUID4
from starlette.status import HTTP_404_NOT_FOUND

from ...autogen.openapi_model import ResourceUpdatedResponse, UpdateUserRequest
from ...common.exceptions.users import UserNotFoundError
from ...dependencies.developer_id import get_developer_id
from ...models.user.update_user import update_user_query
from .router import router


@router.put("/users/{user_id}", tags=["users"])
async def update_user(
    user_id: UUID4,
    request: UpdateUserRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceUpdatedResponse:
    try:
        resp = update_user_query(
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

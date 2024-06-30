from fastapi import APIRouter, HTTPException, Depends
from pydantic import UUID4
from starlette.status import HTTP_404_NOT_FOUND

from agents_api.dependencies.developer_id import get_developer_id
from agents_api.common.exceptions.users import UserNotFoundError
from agents_api.models.user.update_user import update_user_query
from agents_api.autogen.openapi_model import UpdateUserRequest, ResourceUpdatedResponse

router = APIRouter()

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
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=str(e)
        )

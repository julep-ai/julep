from fastapi import APIRouter, HTTPException, Depends
from pydantic import UUID4
from starlette.status import HTTP_202_ACCEPTED

from agents_api.dependencies.developer_id import get_developer_id
from agents_api.common.exceptions.users import UserNotFoundError
from agents_api.models.user.delete_user import delete_user_query
from agents_api.autogen.openapi_model import ResourceDeletedResponse
from agents_api.common.utils.datetime import utcnow

router = APIRouter()

@router.delete("/users/{user_id}", status_code=HTTP_202_ACCEPTED, tags=["users"])
async def delete_user(
    user_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> ResourceDeletedResponse:
    try:
        delete_user_query(x_developer_id, user_id)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    return ResourceDeletedResponse(id=user_id, deleted_at=utcnow())

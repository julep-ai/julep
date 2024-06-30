from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, UUID4
from typing import Optional
from uuid import uuid4

from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.user.create_user import create_user_query
from agents_api.autogen.openapi_model import CreateUserRequest, ResourceCreatedResponse

router = APIRouter()

@router.post("/users", status_code=HTTP_201_CREATED, tags=["users"])
async def create_user(
    request: CreateUserRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    user_id = uuid4()
    created_user = create_user_query(
        developer_id=x_developer_id,
        user_id=user_id,
        name=request.name,
        about=request.about,
        metadata=request.metadata
    )
    return ResourceCreatedResponse(
        id=str(user_id),
        created_at=created_user["created_at"]
    )

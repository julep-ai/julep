from typing import Annotated
from uuid import uuid4
from pydantic import UUID4
from fastapi import APIRouter, HTTPException, status, Header
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED
from memory_api.clients.cozo import client
from memory_api.models.user.create_user import create_user_query
from memory_api.models.user.get_user import get_user_query
from memory_api.models.user.list_users import list_users_query
from memory_api.models.user.update_user import update_user_query
from memory_api.autogen.openapi_model import (
    User,
    CreateUserRequest,
    UpdateUserRequest,
    ResourceCreatedResponse,
    ResourceUpdatedResponse,
)


router = APIRouter()


@router.delete("/users/{user_id}", status_code=HTTP_202_ACCEPTED, tags=["users"])
async def delete_user(user_id: UUID4, x_developer_id: Annotated[UUID4, Header()]):
    try:
        client.rm(
            "users",
            {
                "user_id": str(user_id),
                "developer_id": str(x_developer_id),
            },
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.put("/users/{user_id}", tags=["users"])
async def update_user(
    user_id: UUID4,
    request: UpdateUserRequest,
    x_developer_id: Annotated[UUID4, Header()],
) -> ResourceUpdatedResponse:
    try:
        resp = client.run(
            update_user_query(
                developer_id=x_developer_id,
                user_id=user_id,
                name=request.name,
                about=request.about,
            )
        )

        return ResourceUpdatedResponse(
            id=resp["user_id"][0],
            updated_at=resp["updated_at"][0],
        )
        # TODO: add additional info update
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.post("/users", status_code=HTTP_201_CREATED, tags=["users"])
async def create_user(
    request: CreateUserRequest, x_developer_id: Annotated[UUID4, Header()]
) -> ResourceCreatedResponse:
    user_id = uuid4()
    resp = client.run(
        create_user_query(
            developer_id=x_developer_id,
            user_id=user_id,
            name=request.name,
            about=request.about,
        ),
    )

    # TODO: add additional info
    return ResourceCreatedResponse(
        id=resp["user_id"][0],
        created_at=resp["created_at"][0],
    )


@router.get("/users", tags=["users"])
async def list_users(
    x_developer_id: Annotated[UUID4, Header()], limit: int = 100, offset: int = 0
) -> list[User]:
    # TODO: add additional info
    return [
        User(**row.to_dict())
        for _, row in client.run(
            list_users_query(
                developer_id=x_developer_id,
                limit=limit,
                offset=offset,
            ),
        ).iterrows()
    ]

from pydantic import UUID4
from fastapi import APIRouter, HTTPException, status
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED
from memory_api.clients.cozo import client
from memory_api.models.user.create_user import create_user_query
from memory_api.models.user.get_user import get_user_query
from memory_api.models.user.list_users import list_users_query
from .protocol import User, CreateUserRequest, UpdateUserRequest


router = APIRouter()


@router.delete("/users/{user_id}", status_code=HTTP_202_ACCEPTED)
async def delete_user(user_id: UUID4):
    try:
        client.rm("users", {"user_id": user_id})
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.put("/users/{user_id}")
async def update_user(user_id: UUID4, request: UpdateUserRequest):
    try:
        client.update(
            "users",
            {
                "user_id": user_id,
                "about": request.about,
            },
        )
        # TODO: add additional info update
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.post("/users", status_code=HTTP_201_CREATED)
async def create_user(request: CreateUserRequest) -> User:
    client.run(
        create_user_query.format(
            id=request.id,
            name=request.name,
            email=request.email,
            about=request.about,
        ),
    )

    # TODO: add additional info
    res = [
        row.to_dict()
        for _, row in client.run(
            get_user_query.format(id=request.id),
        ).iterrows()
    ][0]
    return User(**res)


@router.get("/users")
async def list_users(limit: int = 100, offset: int = 0) -> list[User]:
    # TODO: add additional info
    return [
        User(**row.to_dict())
        for _, row in client.run(
            list_users_query.format(
                limit=limit,
                offset=offset,
            ),
        ).iterrows()
    ]

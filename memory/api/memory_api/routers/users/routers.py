from pydantic import UUID4
from fastapi import APIRouter, HTTPException, status
from starlette.status import HTTP_201_CREATED, HTTP_202_ACCEPTED
from memory_api.clients.cozo import client
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
            }
        )
        #TODO: add additional info update
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.post("/users", status_code=HTTP_201_CREATED)
async def create_user(request: CreateUserRequest) -> User:
    create_query = f"""
        ?[user_id, name, email, about, metadata] <- [
            ["{request.id}", "{request.name}", "{request.email}", "{request.about}", {{}}]
        ]
        
        :put users {{
            user_id =>
            name,
            email,
            about,
            metadata,
        }}
    """
    
    client.run(create_query)

    get_query = f"""
        input[user_id] <- [[to_uuid("{request.id}")]]

        ?[
            user_id,
            name,
            email,
            about,
            metadata,
            updated_at,
            created_at,
        ] := input[user_id],
            *users {{
                user_id,
                name,
                email,
                about,
                metadata,
                updated_at: validity,
                created_at,
                @ "NOW"
            }}, updated_at = to_int(validity)"""

    #TODO: add additional info
    res = [row.to_dict() for _, row in client.run(get_query).iterrows()][0]
    return User(**res)


@router.get("/users")
async def list_users(limit: int = 100, offset: int = 0) -> list[User]:
    query = f"""
    ?[
        user_id,
        name,
        email,
        about,
        metadata,
        updated_at,
        created_at,
    ] := *users {{
            user_id,
            name,
            email,
            about,
            metadata,
            updated_at: validity,
            created_at,
            @ "NOW"
        }}, updated_at = to_int(validity)
    
    :limit {limit}
    :offset {offset}
    """

    #TODO: add additional info
    return [User(**row.to_dict()) for _, row in client.run(query).iterrows()]
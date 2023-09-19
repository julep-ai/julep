from fastapi import APIRouter, HTTPException, status
from memory_api.clients.cozo import client
from .protocol import User


router = APIRouter()


@router.get("/users/{email}")
def get_user(email: str) -> User:
    query = f"""
        input[email] <- [[to_uuid("{email}")]]

        ?[
            user_id,
            name,
            email,
            about,
            metadata,
            updated_at,
            created_at,
        ] := input[email],
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

    resp = client.run(query)

    try:
        return User(
            id=resp["user_id"][0],
            name=resp["name"][0],
            email=resp["email"][0],
            about=resp["about"][0],
            metadata=resp["metadata"][0],
            created_at=resp["created_at"][0],
            updated_at=resp["updated_at"][0],
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.post("/users/")
def create_user(user: User) -> User:
    query = f"""
        {{
            ?[user_id, name, email, about, metadata] <- [
                ["{user.id}", "{user.name}", "{user.email}", "{user.about}", {user.metadata}]
            ]
            
            :put users {{
                user_id =>
                name,
                email,
                about,
                metadata,
            }}
        }}

        {{
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
        }}"""
    
    resp = client.run(query)

    try:
        return User(
            id=resp["user_id"][0],
            name=resp["name"][0],
            email=resp["email"][0],
            about=resp["about"][0],
            metadata=resp["metadata"][0],
            created_at=resp["created_at"][0],
            updated_at=resp["updated_at"][0],
        )
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User can not be created",
        )

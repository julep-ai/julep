from fastapi import APIRouter, HTTPException, status
from memory_api.clients.cozo import client
from .protocol import User, UserRequest
from .exceptions import InvalidUserQueryError


router = APIRouter()


@router.get("/users/")
async def get_user(request: UserRequest) -> User:
    if request.user_id is not None:
        query = f"""
            input[email] <- [[to_uuid("{request.user_id}")]]

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
    elif request.email is not None:
        query = f"""
            input[email] <- [["{request.email}"]]

            ?[
                user_id,
                name,
                email,
                about,
                metadata,
                updated_at,
                created_at,
            ] := input[email],
                *users:by_email {{
                    user_id,
                    name,
                    email,
                    about,
                    metadata,
                    updated_at: validity,
                    @ "NOW"
                }}, updated_at = to_int(validity)"""
    else:
        raise InvalidUserQueryError("either user_id or email must be given")

    try:
        res = [row.to_dict() for _, row in client.run(query).iterrows()][0]
        return User(**res)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


@router.post("/users/")
async def create_user(user: User):
    query = f"""
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
    """
    
    client.run(query)

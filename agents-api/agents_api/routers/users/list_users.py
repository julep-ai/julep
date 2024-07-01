import json
from json import JSONDecodeError
from typing import Annotated, List

from fastapi import HTTPException, Depends, status
from pydantic import UUID4

from ...dependencies.developer_id import get_developer_id
from ...models.user.list_users import list_users_query
from ...autogen.openapi_model import User

from .router import router


@router.get("/users", tags=["users"])
async def list_users(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    limit: int = 100,
    offset: int = 0,
    metadata_filter: str = "{}",
) -> List[User]:
    try:
        metadata_filter = json.loads(metadata_filter)
    except JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="metadata_filter is not a valid JSON",
        )

    users = [
        User(**row.to_dict())
        for _, row in list_users_query(
            developer_id=x_developer_id,
            limit=limit,
            offset=offset,
            metadata_filter=metadata_filter,
        ).iterrows()
    ]

    return users

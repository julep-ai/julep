from typing import Annotated

from fastapi import HTTPException, Depends, status
from pycozo.client import QueryException
from pydantic import UUID4

from ...dependencies.developer_id import get_developer_id
from ...models.user.get_user import get_user_query
from ...autogen.openapi_model import User
from ...common.exceptions.users import UserNotFoundError

from .router import router


@router.get("/users/{user_id}", tags=["users"])
async def get_user_details(
    user_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> User:
    try:
        resp = [
            row.to_dict()
            for _, row in get_user_query(
                developer_id=x_developer_id,
                user_id=user_id,
            ).iterrows()
        ][0]

        return User(**resp)
    except (IndexError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except QueryException as e:
        # the code is not so informative now, but it may be a good solution in the future
        if e.code == "transact::assertion_failure":
            raise UserNotFoundError(x_developer_id, user_id)

        raise

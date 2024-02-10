import uuid
from typing import Annotated
from pydantic import UUID4
from fastapi import Header
from fastapi import HTTPException
from starlette.status import HTTP_403_FORBIDDEN


async def get_developer_id(
    x_developer_id: Annotated[str | None, Header()] = None
) -> UUID4:
    invalid_developer = HTTPException(
        status_code=HTTP_403_FORBIDDEN, detail="Invalid developer"
    )

    if x_developer_id is None:
        raise invalid_developer

    try:
        return uuid.UUID(x_developer_id, version=4)
    except ValueError:
        raise invalid_developer

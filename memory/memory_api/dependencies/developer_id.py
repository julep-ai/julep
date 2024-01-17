from typing import Annotated
from pydantic import UUID4
from fastapi import Header
from fastapi import HTTPException
from starlette.status import HTTP_403_FORBIDDEN


async def get_developer_id(x_developer_id: Annotated[UUID4 | None, Header()] = None):
    if x_developer_id is None:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Unknown developer")

    return x_developer_id

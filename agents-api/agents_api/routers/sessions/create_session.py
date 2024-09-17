from typing import Annotated

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    CreateSessionRequest,
    ResourceCreatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from ...models.session.create_session import create_session as create_session_query
from .router import router


@router.post("/sessions", status_code=HTTP_201_CREATED, tags=["sessions"])
async def create_session(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    data: CreateSessionRequest,
) -> ResourceCreatedResponse:
    session = create_session_query(
        developer_id=x_developer_id,
        data=data,
    )

    return ResourceCreatedResponse(
        id=session.id,
        created_at=session.created_at,
        jobs=[],
    )

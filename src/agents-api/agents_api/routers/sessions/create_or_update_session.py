from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import CreateOrUpdateSessionRequest, Session
from ...dependencies.developer_id import get_developer_id
from ...queries.sessions.create_or_update_session import (
    create_or_update_session as create_or_update_session_query,
)
from .router import router


@router.post("/sessions/{session_id}", status_code=HTTP_201_CREATED, tags=["sessions"])
async def create_or_update_session(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    session_id: UUID,
    data: CreateOrUpdateSessionRequest,
) -> Session:
    return await create_or_update_session_query(
        developer_id=x_developer_id,
        session_id=session_id,
        data=data,
    )

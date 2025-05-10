# AIDEV-NOTE: This module defines the API endpoint for creating new sessions.
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import CreateSessionRequest, Session
from ...dependencies.developer_id import get_developer_id
from ...queries.sessions.create_session import create_session as create_session_query
from .router import router


# AIDEV-NOTE: API endpoint to create a new session.
# It depends on the developer ID and the session data from the request body, and calls the create_session_query function.
@router.post("/sessions", status_code=HTTP_201_CREATED, tags=["sessions"])
async def create_session(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    data: CreateSessionRequest,
) -> Session:
    return await create_session_query(
        developer_id=x_developer_id,
        data=data,
    )

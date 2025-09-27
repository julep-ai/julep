# AIDEV-NOTE: This module defines the API endpoint for retrieving a specific session.
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import Session
from ...dependencies.developer_id import get_developer_id
from ...queries.sessions.get_session import get_session as get_session_query
from .router import router


# AIDEV-NOTE: API endpoint to get a session by its ID.
# It depends on the developer ID and the session ID from the path parameter, and calls the get_session_query function.
@router.get("/sessions/{session_id}", tags=["sessions"])
async def get_session(
    session_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> Session:
    return await get_session_query(developer_id=x_developer_id, session_id=session_id)

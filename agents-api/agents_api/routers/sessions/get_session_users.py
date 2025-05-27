"""API endpoint to list users for a session."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import ListResponse, User
from ...dependencies.developer_id import get_developer_id
from ...queries.sessions.get_session_users import get_session_users as get_session_users_query
from .router import router


@router.get("/sessions/{session_id}/users", tags=["sessions"])
async def get_session_users(
    session_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ListResponse[User]:
    """Return users associated with the session."""

    users = await get_session_users_query(
        developer_id=x_developer_id,
        session_id=session_id,
    )
    return ListResponse[User](items=users)

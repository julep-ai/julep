"""API endpoint to list agents for a session."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import Agent, ListResponse
from ...dependencies.developer_id import get_developer_id
from ...queries.sessions.get_session_agents import (
    get_session_agents as get_session_agents_query,
)
from .router import router


@router.get("/sessions/{session_id}/agents", tags=["sessions"])
async def get_session_agents(
    session_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> ListResponse[Agent]:
    """Return agents associated with the session."""

    agents = await get_session_agents_query(
        developer_id=x_developer_id,
        session_id=session_id,
    )
    return ListResponse[Agent](items=agents)

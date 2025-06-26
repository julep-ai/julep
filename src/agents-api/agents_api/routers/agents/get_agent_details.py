# AIDEV-NOTE: This module defines the API endpoint for retrieving a specific agent.
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import Agent
from ...dependencies.developer_id import get_developer_id
from ...queries.agents.get_agent import get_agent as get_agent_query
from .router import router


# AIDEV-NOTE: API endpoint to get an agent by its ID.
# It depends on the developer ID and the agent ID from the path parameter, and calls the get_agent_query function.
@router.get("/agents/{agent_id}", tags=["agents"])
async def get_agent_details(
    agent_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
) -> Agent:
    return await get_agent_query(developer_id=x_developer_id, agent_id=agent_id)

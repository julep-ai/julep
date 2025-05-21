# AIDEV-NOTE: This module defines the API endpoint for creating new agents.
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import (
    Agent,
    CreateAgentRequest,
)
from ...dependencies.developer_id import get_developer_id
from ...queries.agents.create_agent import create_agent as create_agent_query
from ..utils.model_validation import validate_model
from .router import router


# AIDEV-NOTE: API endpoint to create a new agent.
# It depends on the developer ID and the agent data from the request body.
# Validates the agent model if specified and calls the create_agent_query function.
@router.post("/agents", status_code=HTTP_201_CREATED, tags=["agents"])
async def create_agent(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    data: CreateAgentRequest,
) -> Agent:
    if data.model:
        await validate_model(data.model)

    return await create_agent_query(
        developer_id=x_developer_id,
        data=data,
    )

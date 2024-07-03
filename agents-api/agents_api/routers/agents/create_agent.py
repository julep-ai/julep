from typing import Annotated
from uuid import uuid4

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_201_CREATED

from ...dependencies.developer_id import get_developer_id
from ...models.agent.create_agent import create_agent_query
from ...autogen.openapi_model import CreateAgentRequest, ResourceCreatedResponse
from ...common.utils.datetime import utcnow

from .router import router


@router.post("/agents", status_code=HTTP_201_CREATED, tags=["agents"])
async def create_agent(
    request: CreateAgentRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceCreatedResponse:
    agent_id = request.agent_id if request.agent_id else uuid4()
    created_agent = create_agent_query(
        developer_id=x_developer_id,
        agent_id=agent_id,
        name=request.name,
        about=request.about,
        instructions=request.instructions,
        model=request.model,
        default_settings=request.default_settings,
        metadata=request.metadata,
    )
    return ResourceCreatedResponse(id=str(agent_id), created_at=utcnow())

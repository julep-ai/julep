from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4
from starlette.status import HTTP_404_NOT_FOUND, HTTP_200_OK

from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.agent.update_agent import update_agent_query
from agents_api.common.exceptions.agents import AgentNotFoundError
from agents_api.autogen.openapi_model import UpdateAgentRequest, ResourceUpdatedResponse

router = APIRouter()

@router.put("/agents/{agent_id}", response_model=ResourceUpdatedResponse, status_code=HTTP_200_OK, tags=["agents"])
async def update_agent(
    agent_id: UUID4,
    request: UpdateAgentRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceUpdatedResponse:
    try:
        updated_agent = update_agent_query(
            agent_id=agent_id,
            developer_id=x_developer_id,
            name=request.name,
            about=request.about,
            model=request.model,
            default_settings=request.default_settings,
            metadata=request.metadata,
            instructions=request.instructions,
        )
        return ResourceUpdatedResponse(**updated_agent)
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=str(e)
        )

from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4
from starlette.status import HTTP_404_NOT_FOUND

from agents_api.dependencies.developer_id import get_developer_id
from agents_api.models.agent.get_agent import get_agent_query
from agents_api.common.exceptions.agents import AgentNotFoundError
from agents_api.autogen.openapi_model import Agent

router = APIRouter()

@router.get("/agents/{agent_id}", tags=["agents"])
async def get_agent_details(
    agent_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> Agent:
    try:
        agent = get_agent_query(developer_id=x_developer_id, agent_id=agent_id)
        if not agent:
            raise AgentNotFoundError(f"Agent with ID {agent_id} not found")
        return Agent(**agent)
    except AgentNotFoundError as e:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=str(e)
        )

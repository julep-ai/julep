from typing import Annotated

from fastapi import Depends, HTTPException
from pydantic import UUID4
from starlette.status import HTTP_404_NOT_FOUND

from ...dependencies.developer_id import get_developer_id
from ...models.agent.get_agent import get_agent_query
from ...common.exceptions.agents import AgentNotFoundError
from ...autogen.openapi_model import Agent

from .router import router


@router.get("/agents/{agent_id}", tags=["agents"])
async def get_agent_details(
    agent_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> Agent:
    try:
        agent = get_agent_query(developer_id=x_developer_id, agent_id=agent_id)
        if not agent:
            raise AgentNotFoundError(x_developer_id, agent_id)
        return Agent(**agent)
    except AgentNotFoundError as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))

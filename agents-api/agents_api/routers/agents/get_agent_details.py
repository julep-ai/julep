from typing import Annotated

from fastapi import Depends
from pydantic import UUID4

from ...autogen.openapi_model import Agent
from ...dependencies.developer_id import get_developer_id
from ...models.agent.get_agent import get_agent as get_agent_query
from .router import router


@router.get("/agents/{agent_id}", tags=["agents"])
async def get_agent_details(
    agent_id: UUID4,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> Agent:
    return get_agent_query(developer_id=x_developer_id, agent_id=agent_id)

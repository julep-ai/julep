from typing import Annotated

from fastapi import Depends, HTTPException
from pydantic import UUID4
from starlette.status import HTTP_202_ACCEPTED, HTTP_404_NOT_FOUND

from ...dependencies.developer_id import get_developer_id
from ...models.agent.delete_agent import delete_agent_query
from ...common.exceptions.agents import AgentNotFoundError
from ...common.utils.datetime import utcnow
from ...autogen.openapi_model import ResourceDeletedResponse

from .router import router


@router.delete("/agents/{agent_id}", status_code=HTTP_202_ACCEPTED, tags=["agents"])
async def delete_agent(
    agent_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> ResourceDeletedResponse:
    try:
        delete_agent_query(x_developer_id, agent_id)
    except AgentNotFoundError as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))
    return ResourceDeletedResponse(id=agent_id, deleted_at=utcnow())

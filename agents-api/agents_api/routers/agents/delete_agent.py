from typing import Annotated

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_202_ACCEPTED

from ...autogen.openapi_model import ResourceDeletedResponse
from ...dependencies.developer_id import get_developer_id
from ...models.agent.delete_agent import delete_agent as delete_agent_query
from .router import router


@router.delete("/agents/{agent_id}", status_code=HTTP_202_ACCEPTED, tags=["agents"])
async def delete_agent(
    agent_id: UUID4, x_developer_id: Annotated[UUID4, Depends(get_developer_id)]
) -> ResourceDeletedResponse:
    return delete_agent_query(developer_id=x_developer_id, agent_id=agent_id)

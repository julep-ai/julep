from typing import Annotated

from fastapi import Depends
from uuid import UUID
from starlette.status import HTTP_200_OK

from ...autogen.openapi_model import ResourceUpdatedResponse, UpdateAgentRequest
from ...dependencies.developer_id import get_developer_id
from ...models.agent.update_agent import update_agent as update_agent_query
from .router import router


@router.put(
    "/agents/{agent_id}",
    response_model=ResourceUpdatedResponse,
    status_code=HTTP_200_OK,
    tags=["agents"],
)
async def update_agent(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    agent_id: UUID,
    data: UpdateAgentRequest,
) -> ResourceUpdatedResponse:
    return update_agent_query(
        developer_id=x_developer_id,
        agent_id=agent_id,
        data=data,
    )

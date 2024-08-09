from typing import Annotated

from fastapi import Depends
from pydantic import UUID4
from starlette.status import HTTP_200_OK

from ...autogen.openapi_model import PatchAgentRequest, ResourceUpdatedResponse
from ...dependencies.developer_id import get_developer_id
from ...models.agent.patch_agent import patch_agent as patch_agent_query
from .router import router


@router.patch(
    "/agents/{agent_id}",
    response_model=ResourceUpdatedResponse,
    status_code=HTTP_200_OK,
    tags=["agents"],
)
async def patch_agent(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    agent_id: UUID4,
    data: PatchAgentRequest,
) -> ResourceUpdatedResponse:
    return patch_agent_query(
        agent_id=agent_id,
        developer_id=x_developer_id,
        data=data,
    )

from typing import Annotated

from fastapi import Depends, HTTPException
from pydantic import UUID4
from starlette.status import HTTP_404_NOT_FOUND, HTTP_200_OK

from ...dependencies.developer_id import get_developer_id
from ...models.agent.patch_agent import patch_agent_query
from ...common.exceptions.agents import AgentNotFoundError
from ...autogen.openapi_model import PatchAgentRequest, ResourceUpdatedResponse

from .router import router


@router.patch(
    "/agents/{agent_id}",
    response_model=ResourceUpdatedResponse,
    status_code=HTTP_200_OK,
    tags=["agents"],
)
async def patch_agent(
    agent_id: UUID4,
    request: PatchAgentRequest,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceUpdatedResponse:
    try:
        updated_agent = patch_agent_query(
            agent_id=agent_id,
            developer_id=x_developer_id,
            default_settings=request.default_settings,
            name=request.name,
            about=request.about,
            model=request.model,
            metadata=request.metadata,
            instructions=request.instructions,
        )
        return ResourceUpdatedResponse(**updated_agent)
    except AgentNotFoundError as e:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail=str(e))

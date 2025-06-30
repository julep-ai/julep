from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_200_OK

from ...autogen.openapi_model import Agent, PatchAgentRequest
from ...dependencies.developer_id import get_developer_id
from ...queries.agents.patch_agent import patch_agent as patch_agent_query
from ..utils.model_validation import validate_model
from .router import router


@router.patch(
    "/agents/{agent_id}",
    response_model=Agent,
    status_code=HTTP_200_OK,
    tags=["agents"],
)
async def patch_agent(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    agent_id: UUID,
    data: PatchAgentRequest,
) -> Agent:
    if data.model:
        await validate_model(data.model)

    return await patch_agent_query(
        agent_id=agent_id,
        developer_id=x_developer_id,
        data=data,
    )

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_200_OK

from ...autogen.openapi_model import Agent, UpdateAgentRequest
from ...dependencies.developer_id import get_developer_id
from ...queries.agents.update_agent import update_agent as update_agent_query
from ..utils.model_validation import validate_model
from .router import router


@router.put(
    "/agents/{agent_id}",
    response_model=Agent,
    status_code=HTTP_200_OK,
    tags=["agents"],
)
async def update_agent(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    agent_id: UUID,
    data: UpdateAgentRequest,
) -> Agent:
    if data.model:
        await validate_model(data.model)

    return await update_agent_query(
        developer_id=x_developer_id,
        agent_id=agent_id,
        data=data,
    )

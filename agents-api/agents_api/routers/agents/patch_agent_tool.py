from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import (
    PatchToolRequest,
    ResourceUpdatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from ...models.tools.patch_tool import patch_tool as patch_tool_query
from .router import router


@router.patch("/agents/{agent_id}/tools/{tool_id}", tags=["agents"])
async def patch_agent_tool(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    agent_id: UUID,
    tool_id: UUID,
    data: PatchToolRequest,
) -> ResourceUpdatedResponse:
    return patch_tool_query(
        developer_id=x_developer_id,
        agent_id=agent_id,
        tool_id=tool_id,
        data=data,
    )

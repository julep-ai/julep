from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import UUID4

from ...autogen.openapi_model import (
    PatchToolRequest,
    ResourceUpdatedResponse,
)
from ...dependencies.developer_id import get_developer_id
from ...models.tools.patch_tool import patch_tool as patch_tool_query
from .router import router


@router.patch("/agents/{agent_id}/tools/{tool_id}", tags=["agents"])
async def patch_agent_tools(
    agent_id: UUID,
    tool_id: UUID,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    patch_tool: PatchToolRequest,
) -> ResourceUpdatedResponse:
    _, resp = next(
        patch_tool_query(
            developer_id=x_developer_id,
            agent_id=agent_id,
            tool_id=tool_id,
            patch_tool=patch_tool,
        ).iterrows()
    )

    return ResourceUpdatedResponse(id=resp["tool_id"], updated_at=resp["updated_at"])

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import UUID4

from ...autogen.openapi_model import (
    ResourceUpdatedResponse,
    UpdateToolRequest,
)
from ...dependencies.developer_id import get_developer_id
from ...models.tools.update_tool import update_tool as update_tool_query
from .router import router


@router.put("/agents/{agent_id}/tools/{tool_id}", tags=["agents"])
async def update_agent_tools(
    agent_id: UUID,
    tool_id: UUID,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    data: UpdateToolRequest,
) -> ResourceUpdatedResponse:
    _, resp = next(
        update_tool_query(
            developer_id=x_developer_id,
            agent_id=agent_id,
            tool_id=tool_id,
            data=data,
        ).iterrows()
    )

    return ResourceUpdatedResponse(id=resp["tool_id"], updated_at=resp["updated_at"])

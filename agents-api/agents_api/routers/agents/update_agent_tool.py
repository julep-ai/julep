from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import Tool, UpdateToolRequest
from ...common.utils.tool_validation import validate_tool
from ...dependencies.developer_id import get_developer_id
from ...queries.tools.update_tool import update_tool as update_tool_query
from .router import router


@router.put("/agents/{agent_id}/tools/{tool_id}", tags=["agents"])
async def update_agent_tool(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    agent_id: UUID,
    tool_id: UUID,
    data: UpdateToolRequest,
) -> Tool:
    await validate_tool(data)

    return await update_tool_query(
        developer_id=x_developer_id,
        agent_id=agent_id,
        tool_id=tool_id,
        data=data,
    )

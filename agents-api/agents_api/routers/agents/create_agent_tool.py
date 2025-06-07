from typing import Annotated
from uuid import UUID

from fastapi import Depends
from starlette.status import HTTP_201_CREATED

from ...autogen.openapi_model import CreateToolRequest, Tool
from ...common.utils.tool_validation import validate_tool
from ...dependencies.developer_id import get_developer_id
from ...queries.tools.create_tools import create_tools as create_tools_query
from .router import router


@router.post("/agents/{agent_id}/tools", status_code=HTTP_201_CREATED, tags=["agents"])
async def create_agent_tool(
    agent_id: UUID,
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    data: CreateToolRequest,
) -> Tool:
    await validate_tool(data)

    tools = await create_tools_query(
        developer_id=x_developer_id,
        agent_id=agent_id,
        data=[data],
    )

    return tools[0]

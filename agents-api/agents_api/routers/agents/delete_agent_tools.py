from typing import Annotated
from uuid import UUID

from fastapi import Depends
from pydantic import UUID4

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ...dependencies.developer_id import get_developer_id
from ...models.tools.delete_tools import delete_tool as delete_tool_query
from .router import router


@router.delete("/agents/{agent_id}/tools/{tool_id}", tags=["agents"])
async def delete_agent_tools(
    agent_id: UUID,
    tool_id: UUID,
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
) -> ResourceDeletedResponse:
    _, resp = next(
        delete_tool_query(
            developer_id=x_developer_id,
            agent_id=agent_id,
            tool_id=tool_id,
        ).iterrows()
    )

    return ResourceDeletedResponse(id=resp["tool_id"], deleted_at=utcnow())

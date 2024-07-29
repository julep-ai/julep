from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import (
    PatchToolRequest,
    ResourceUpdatedResponse,
    UpdateToolRequest,
)
from .patch_tool import patch_tool


@beartype
def update_tool(
    *,
    developer_id: UUID,
    agent_id: UUID,
    tool_id: UUID,
    data: UpdateToolRequest,
    **kwargs,
) -> ResourceUpdatedResponse:
    # Same as patch_tool_query, but with a different request payload
    return patch_tool(
        developer_id=developer_id,
        agent_id=agent_id,
        tool_id=tool_id,
        patch_tool=PatchToolRequest(**data.model_dump()),
        **kwargs,
    )

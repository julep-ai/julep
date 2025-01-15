from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import PatchToolRequest, ResourceUpdatedResponse
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import increase_counter
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for patching a tool
tools_query = """
WITH updated_tools AS (
    UPDATE tools
    SET
        type = COALESCE($4, type),
        name = COALESCE($5, name),
        description = COALESCE($6, description),
        spec = COALESCE($7, spec)
    WHERE
        developer_id = $1 AND
        agent_id = $2 AND
        tool_id = $3
    RETURNING *
)
SELECT * FROM updated_tools;
"""


@rewrap_exceptions(common_db_exceptions("tool", ["patch"]))
@wrap_in_class(
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {"id": d["tool_id"], "jobs": [], **d},
)
@increase_counter("patch_tool")
@pg_query
@beartype
async def patch_tool(
    *, developer_id: UUID, agent_id: UUID, tool_id: UUID, data: PatchToolRequest
) -> tuple[str, list]:
    """
    Updates the tool information for a given agent and tool ID in the 'PostgreSQL' database.

    Parameters:
        agent_id (UUID): The unique identifier of the agent.
        tool_id (UUID): The unique identifier of the tool to be updated.
        data (PatchToolRequest): The request payload containing the updated tool information.
    Returns:
        ResourceUpdatedResponse: The updated tool data.
    """

    developer_id = str(developer_id)
    agent_id = str(agent_id)
    tool_id = str(tool_id)

    # Extract the tool data from the payload
    patch_data = data.model_dump(exclude_none=True)

    # Assert that only one of the tool type fields is present
    tool_specs = [
        (tool_type, patch_data.get(tool_type))
        for tool_type in ["function", "integration", "system", "api_call"]
        if patch_data.get(tool_type) is not None
    ]

    assert len(tool_specs) <= 1, "Invalid tool update"
    tool_type, tool_spec = tool_specs[0] if tool_specs else (None, None)

    if tool_type is not None:
        patch_data["type"] = patch_data.get("type", tool_type)
        assert patch_data["type"] == tool_type, "Invalid tool update"

    tool_spec = tool_spec or {}
    if tool_spec:
        del patch_data[tool_type]

    return (
        tools_query,
        [
            developer_id,
            agent_id,
            tool_id,
            tool_type,
            data.name,
            data.description,
            tool_spec,
        ],
    )

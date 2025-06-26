from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Tool, UpdateToolRequest
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for updating a tool
tools_query = """
UPDATE tools
SET
    type = $4,
    name = $5,
    description = $6,
    spec = $7
WHERE
    developer_id = $1 AND
    agent_id = $2 AND
    tool_id = $3
RETURNING *;
"""


@rewrap_exceptions(common_db_exceptions("tool", ["update"]))
@wrap_in_class(
    Tool,
    one=True,
    transform=lambda d: {"id": d["tool_id"], "jobs": [], **d},
)
@query_metrics("update_tool")
@pg_query
@beartype
async def update_tool(
    *,
    developer_id: UUID,
    agent_id: UUID,
    tool_id: UUID,
    data: UpdateToolRequest,
    **kwargs,
) -> tuple[str, list]:
    developer_id = str(developer_id)
    agent_id = str(agent_id)
    tool_id = str(tool_id)

    # Extract the tool data from the payload
    update_data = data.model_dump(exclude_none=True)

    # Assert that only one of the tool type fields is present
    tool_specs = [
        (tool_type, update_data.get(tool_type))
        for tool_type in ["function", "integration", "system", "api_call"]
        if update_data.get(tool_type) is not None
    ]

    assert len(tool_specs) <= 1, "Invalid tool update"
    tool_type, tool_spec = tool_specs[0] if tool_specs else (None, None)

    if tool_type is not None:
        update_data["type"] = update_data.get("type", tool_type)
        assert update_data["type"] == tool_type, "Invalid tool update"

    update_data["spec"] = tool_spec
    del update_data[tool_type]

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

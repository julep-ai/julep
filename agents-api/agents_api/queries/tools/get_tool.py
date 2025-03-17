from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Tool
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for getting a tool
tools_query = """
SELECT
    tool_id, name, description, type, spec,
    developer_id, agent_id, created_at, updated_at
FROM tools
WHERE
    developer_id = $1 AND
    agent_id = $2 AND
    tool_id = $3
LIMIT 1
"""


@rewrap_exceptions(common_db_exceptions("tool", ["get"]))
@wrap_in_class(
    Tool,
    transform=lambda d: {
        "id": d.pop("tool_id"),
        d["type"]: d.pop("spec"),
        **d,
    },
    one=True,
)
@pg_query
@beartype
async def get_tool(
    *,
    developer_id: UUID,
    agent_id: UUID,
    tool_id: UUID,
) -> tuple[str, list]:
    developer_id = str(developer_id)
    agent_id = str(agent_id)
    tool_id = str(tool_id)

    return (
        tools_query,
        [
            developer_id,
            agent_id,
            tool_id,
        ],
    )

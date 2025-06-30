"""This module contains functions for creating tools in the PostgreSQL database."""

from uuid import UUID

from beartype import beartype
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateToolRequest, Tool
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for creating tools
tools_query = """INSERT INTO tools
(
    developer_id,
    agent_id,
    tool_id,
    type,
    name,
    spec,
    description
)
SELECT
	$1,
    $2,
    $3,
    $4,
    $5,
    $6,
    $7
WHERE NOT EXISTS (
	SELECT null FROM tools
	WHERE (agent_id, name) = ($2, $5)
)
RETURNING *
"""


@rewrap_exceptions(common_db_exceptions("tool", ["create"]))
@wrap_in_class(
    Tool,
    transform=lambda d: {
        "id": d.pop("tool_id"),
        d["type"]: d.pop("spec"),
        **d,
    },
)
@query_metrics("create_tools")
@pg_query
@beartype
async def create_tools(
    *,
    developer_id: UUID,
    agent_id: UUID,
    data: list[CreateToolRequest],
) -> tuple[str, list, str]:
    """
    Constructs an SQL query for inserting tool records into the 'tools' relation in the PostgreSQL database.

    Parameters:
        developer_id (UUID): The unique identifier for the developer.
        agent_id (UUID): The unique identifier for the agent.
        data (list[CreateToolRequest]): A list of function definitions to be inserted.

    Returns:
        list[Tool]
    """

    assert all(
        getattr(tool, tool.type) is not None for tool in data if hasattr(tool, tool.type)
    ), "Tool spec must be passed"

    tools_data = [
        [
            developer_id,
            str(agent_id),
            str(uuid7()),
            tool.type,
            tool.name,
            getattr(tool, tool.type) and getattr(tool, tool.type).model_dump(mode="json"),
            tool.description if hasattr(tool, "description") else None,
        ]
        for tool in data
    ]

    return (
        tools_query,
        tools_data,
        "fetchmany",
    )

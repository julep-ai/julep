"""This module contains functions for creating tools in the CozoDB database."""

from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateToolRequest, Tool
from ...metrics.counters import increase_counter
from ..utils import (
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

# Define the raw SQL query for creating tools
tools_query = parse_one("""INSERT INTO tools
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
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.UniqueViolationError: partialclass(
            HTTPException,
            status_code=409,
            detail="A tool with this name already exists for this agent",
        ),
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="Agent not found",
        ),
    }
)
@wrap_in_class(
    Tool,
    transform=lambda d: {
        "id": d.pop("tool_id"),
        d["type"]: d.pop("spec"),
        **d,
    },
)
@pg_query
@increase_counter("create_tools")
@beartype
async def create_tools(
    *,
    developer_id: UUID,
    agent_id: UUID,
    data: list[CreateToolRequest],
    ignore_existing: bool = False,  # TODO: what to do with this flag?
) -> tuple[str, list, str]:
    """
    Constructs a datalog query for inserting tool records into the 'agent_functions' relation in the CozoDB.

    Parameters:
        agent_id (UUID): The unique identifier for the agent.
        data (list[CreateToolRequest]): A list of function definitions to be inserted.

    Returns:
        list[Tool]
    """

    assert all(
        getattr(tool, tool.type) is not None
        for tool in data
        if hasattr(tool, tool.type)
    ), "Tool spec must be passed"

    tools_data = [
        [
            developer_id,
            str(agent_id),
            str(uuid7()),
            tool.type,
            tool.name,
            getattr(tool, tool.type) and getattr(tool, tool.type).model_dump(),
            tool.description if hasattr(tool, "description") else None,
        ]
        for tool in data
    ]

    return (
        tools_query,
        tools_data,
        "fetchmany",
    )

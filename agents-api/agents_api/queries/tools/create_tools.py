"""This module contains functions for creating tools in the CozoDB database."""

from typing import Any, TypeVar
from uuid import UUID

import sqlvalidator
from beartype import beartype
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateToolRequest, Tool
from ...exceptions import InvalidSQLQuery
from ...metrics.counters import increase_counter
from ..utils import (
    pg_query,
    # rewrap_exceptions,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


sql_query = sqlvalidator.parse(
    """INSERT INTO tools
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
)

if not sql_query.is_valid():
    raise InvalidSQLQuery("create_tools")


# @rewrap_exceptions(
#     {
#         ValidationError: partialclass(HTTPException, status_code=400),
#         TypeError: partialclass(HTTPException, status_code=400),
#         AssertionError: partialclass(HTTPException, status_code=400),
#     }
# )
@wrap_in_class(
    Tool,
    transform=lambda d: {
        "id": UUID(d.pop("tool_id")),
        d["type"]: d.pop("spec"),
        **d,
    },
    _kind="inserted",
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
) -> tuple[list[str], list]:
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
        sql_query.format(),
        tools_data,
        "fetchmany",
    )

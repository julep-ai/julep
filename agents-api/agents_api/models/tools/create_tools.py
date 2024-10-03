"""This module contains functions for creating tools in the CozoDB database."""

from typing import Any, TypeVar
from uuid import UUID, uuid4

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import CreateToolRequest, Tool
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    Tool,
    transform=lambda d: {
        "id": UUID(d.pop("tool_id")),
        d["type"]: d.pop("spec"),
        **d,
    },
    _kind="inserted",
)
@cozo_query
@beartype
def create_tools(
    *,
    developer_id: UUID,
    agent_id: UUID,
    data: list[CreateToolRequest],
    ignore_existing: bool = False,
) -> tuple[list[str], dict]:
    """
    Constructs a datalog query for inserting tool records into the 'agent_functions' relation in the CozoDB.

    Parameters:
    - agent_id (UUID): The unique identifier for the agent.
    - data (list[CreateToolRequest]): A list of function definitions to be inserted.

    Returns:
    list[Tool]
    """

    tools_data = [
        [
            str(agent_id),
            str(uuid4()),
            tool.type,
            tool.name,
            getattr(tool, tool.type).dict(),
        ]
        for tool in data
    ]

    ensure_tool_name_unique_query = """
        input[agent_id, tool_id, type, name, spec] <- $records
        ?[tool_id] :=
            input[agent_id, _, type, name, _],
            *tools{
                agent_id: to_uuid(agent_id),
                tool_id,
                type,
                name,
            }

        :limit 1
        :assert none
    """

    # Datalog query for inserting new tool records into the 'agent_functions' relation
    create_query = """
        input[agent_id, tool_id, type, name, spec] <- $records
        
        # Do not add duplicate
        ?[agent_id, tool_id, type, name, spec] :=
            input[agent_id, tool_id, type, name, spec],
            not *tools{
                agent_id: to_uuid(agent_id),
                type,
                name,
            }

        :insert tools {
            agent_id,
            tool_id,
            type,
            name,
            spec,
        }
        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "agents", agent_id=agent_id),
        create_query,
    ]

    if not ignore_existing:
        queries.insert(
            -1,
            ensure_tool_name_unique_query,
        )

    return (queries, {"records": tools_data})

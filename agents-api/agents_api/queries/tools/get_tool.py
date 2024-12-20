from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import Tool
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
    one=True,
)
@cozo_query
@beartype
def get_tool(
    *,
    developer_id: UUID,
    agent_id: UUID,
    tool_id: UUID,
) -> tuple[list[str], dict]:
    agent_id = str(agent_id)
    tool_id = str(tool_id)

    get_query = """
        input[agent_id, tool_id] <- [[to_uuid($agent_id), to_uuid($tool_id)]]

        ?[
            agent_id,
            tool_id,
            type,
            name,
            spec,
            updated_at,
            created_at,
        ] := input[agent_id, tool_id],
            *tools {
                agent_id,
                tool_id,
                name,
                type,
                spec,
                updated_at,
                created_at,
            }

        :limit 1
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "agents", agent_id=agent_id),
        get_query,
    ]

    return (queries, {"agent_id": agent_id, "tool_id": tool_id})

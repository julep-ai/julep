from typing import Any, Literal, TypeVar
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
        d["type"]: {
            **d.pop("spec"),
            "name": d["name"],
            "description": d["description"],
        },
        **d,
    },
)
@cozo_query
@beartype
def list_tools(
    *,
    developer_id: UUID,
    agent_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> tuple[list[str], dict]:
    agent_id = str(agent_id)

    sort = f"{'-' if direction == 'desc' else ''}{sort_by}"

    list_query = f"""
        input[agent_id] <- [[to_uuid($agent_id)]]

        ?[
            agent_id,
            id,
            name,
            type,
            spec,
            description,
            updated_at,
            created_at,
        ] := input[agent_id],
            *tools {{
                agent_id,
                tool_id: id,
                name,
                type,
                spec,
                description,
                updated_at,
                created_at,
            }}

        :limit $limit
        :offset $offset
        :sort {sort}
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "agents", agent_id=agent_id),
        list_query,
    ]

    return (
        queries,
        {"agent_id": agent_id, "limit": limit, "offset": offset},
    )

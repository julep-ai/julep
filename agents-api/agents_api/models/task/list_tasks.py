from typing import Any, Literal, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)
from .create_task import spec_to_task

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(spec_to_task)
@cozo_query
@beartype
def list_tasks(
    *,
    developer_id: UUID,
    agent_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> tuple[list[str], dict]:
    sort = f"{'-' if direction == 'desc' else ''}{sort_by}"

    list_query = f"""
    input[agent_id] <- [[to_uuid($agent_id)]]

    task_data[
        task_id,
        agent_id,
        name,
        description,
        input_schema,
        tools,
        inherit_tools,
        workflows,
        created_at,
        updated_at,
        metadata,
    ] := 
        input[agent_id],
        *tasks {{
            agent_id,
            task_id,
            updated_at_ms,
            name,
            description,
            input_schema,
            tools,
            inherit_tools,
            workflows,
            created_at,
            metadata,
            @ 'END'
        }},
        updated_at = to_int(updated_at_ms) / 1000

    ?[
        task_id,
        agent_id,
        name,
        description,
        input_schema,
        tools,
        inherit_tools,
        workflows,
        created_at,
        updated_at,
        metadata,
    ] := 
        task_data[
            task_id,
            agent_id,
            name,
            description,
            input_schema,
            tools,
            inherit_tools,
            workflows,
            created_at,
            updated_at,
            metadata,
        ]

    :limit $limit
    :offset $offset
    :sort {sort}
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "agents", agent_id=agent_id),
        list_query,
    ]

    return (queries, {"agent_id": str(agent_id), "limit": limit, "offset": offset})

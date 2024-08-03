from typing import Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import Execution
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(Execution)
@cozo_query
@beartype
def list_executions(
    *,
    developer_id: UUID,
    task_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> tuple[list[str], dict]:
    sort = f"{'-' if direction == 'desc' else ''}{sort_by}"

    list_query = f"""
    input[task_id] <- [[to_uuid($task_id)]]

    ?[
        id,
        task_id,
        status,
        input,
        session_id,
        metadata,
        created_at,
        updated_at,
    ] := input[task_id],
        *executions {{
            task_id,
            execution_id: id,
            status,
            input,
            session_id,
            metadata,
            created_at,
            updated_at,
        }}

    :limit {limit}
    :offset {offset}
    :sort {sort}
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id,
            "tasks",
            task_id=task_id,
            parents=[("agents", "agent_id")],
        ),
        list_query,
    ]

    return (queries, {"task_id": str(task_id), "limit": limit, "offset": offset})

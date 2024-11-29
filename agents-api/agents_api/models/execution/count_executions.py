from typing import Any, TypeVar
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

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(dict, one=True)
@cozo_query
@beartype
def count_executions(
    *,
    developer_id: UUID,
    task_id: UUID,
) -> tuple[list[str], dict]:
    count_query = """
    input[task_id] <- [[to_uuid($task_id)]]

    counter[count(id)] :=
        input[task_id],
        *executions {
            task_id,
            execution_id: id,
        }

    ?[count] := counter[count]
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id,
            "tasks",
            task_id=task_id,
            parents=[("agents", "agent_id")],
        ),
        count_query,
    ]

    return (queries, {"task_id": str(task_id)})

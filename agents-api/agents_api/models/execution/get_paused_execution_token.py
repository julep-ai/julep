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
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
        AssertionError: partialclass(HTTPException, status_code=500),
    }
)
@wrap_in_class(dict, one=True)
@cozo_query
@beartype
def get_paused_execution_token(
    *,
    developer_id: UUID,
    execution_id: UUID,
) -> tuple[list[str], dict]:
    execution_id = str(execution_id)

    check_status_query = """
    ?[execution_id, status] :=
        *executions {
            execution_id,
            status,
        },
        execution_id = to_uuid($execution_id),
        status = "awaiting_input"

    :limit 1
    :assert some
    """

    get_query = """
    ?[task_token, created_at, metadata] :=
        execution_id = to_uuid($execution_id),
        *executions {
            execution_id,
        },
        *transitions {
            execution_id,
            created_at,
            task_token,
            type,
            metadata,
        },
        type = "wait"

    :sort -created_at
    :limit 1
    """

    queries = [
        verify_developer_id_query(developer_id),
        check_status_query,
        get_query,
    ]

    return (queries, {"execution_id": execution_id})

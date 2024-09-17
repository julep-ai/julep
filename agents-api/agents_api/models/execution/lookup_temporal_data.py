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
def lookup_temporal_data(
    *,
    developer_id: UUID,
    execution_id: UUID,
) -> tuple[list[str], dict]:
    developer_id = str(developer_id)
    execution_id = str(execution_id)

    temporal_query = """
    ?[id] :=
      execution_id = to_uuid($execution_id),
      *temporal_executions_lookup {
        id, execution_id, run_id, first_execution_run_id, result_run_id
      }
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id,
            "executions",
            execution_id=execution_id,
            parents=[("agents", "agent_id"), ("tasks", "task_id")],
        ),
        temporal_query,
    ]

    return (
        queries,
        {
            "execution_id": str(execution_id),
        },
    )

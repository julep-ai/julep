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
def get_temporal_workflow_data(
    *,
    execution_id: UUID,
) -> tuple[str, dict]:
    # Executions are allowed direct GET access if they have execution_id

    query = """
      input[execution_id] <- [[to_uuid($execution_id)]]

      ?[id, run_id, result_run_id, first_execution_run_id] := 
          input[execution_id],
          *temporal_executions_lookup {
              execution_id,
              id,
              run_id,
              result_run_id,
              first_execution_run_id,
          }
    """

    return (
        query,
        {
            "execution_id": str(execution_id),
        },
    )

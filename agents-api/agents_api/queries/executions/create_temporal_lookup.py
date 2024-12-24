from typing import TypeVar
from uuid import UUID

from beartype import beartype
from temporalio.client import WorkflowHandle

from ...metrics.counters import increase_counter
from ..utils import (
    pg_query,
)

T = TypeVar("T")

sql_query = """
INSERT INTO temporal_executions_lookup
(
    execution_id,
    id,
    run_id,
    first_execution_run_id,
    result_run_id
)
VALUES
(
    $1,
    $2,
    $3,
    $4,
    $5
)
RETURNING *;
"""


# @rewrap_exceptions(
#     {
#         AssertionError: partialclass(HTTPException, status_code=404),
#         QueryException: partialclass(HTTPException, status_code=400),
#         ValidationError: partialclass(HTTPException, status_code=400),
#         TypeError: partialclass(HTTPException, status_code=400),
#     }
# )
@pg_query
@increase_counter("create_temporal_lookup")
@beartype
async def create_temporal_lookup(
    *,
    developer_id: UUID,  # TODO: what to do with this parameter?
    execution_id: UUID,
    workflow_handle: WorkflowHandle,
) -> tuple[list[str], dict]:
    developer_id = str(developer_id)
    execution_id = str(execution_id)

    return (
        sql_query,
        [
            execution_id,
            workflow_handle.id,
            workflow_handle.run_id,
            workflow_handle.first_execution_run_id,
            workflow_handle.result_run_id,
        ],
    )

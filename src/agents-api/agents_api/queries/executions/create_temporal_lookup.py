from uuid import UUID

from beartype import beartype
from temporalio.client import WorkflowHandle

from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions

# Query to create a temporal lookup
create_temporal_lookup_query = """
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


@rewrap_exceptions(common_db_exceptions("temporal_execution", ["create"]))
@query_metrics("create_temporal_lookup")
@pg_query
@beartype
async def create_temporal_lookup(
    *,
    execution_id: UUID,
    workflow_handle: WorkflowHandle,
) -> tuple[str, list]:
    """
    Create a temporal lookup for a given execution.

    Parameters:
        execution_id (UUID): The ID of the execution.
        workflow_handle (WorkflowHandle): The workflow handle.

    Returns:
        tuple[str, list]: SQL query and parameters for creating the temporal lookup.
    """
    execution_id = str(execution_id)

    return (
        create_temporal_lookup_query,
        [
            execution_id,
            workflow_handle.id,
            workflow_handle.run_id,
            workflow_handle.first_execution_run_id,
            workflow_handle.result_run_id,
        ],
    )

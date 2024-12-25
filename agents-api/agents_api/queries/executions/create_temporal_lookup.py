from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from temporalio.client import WorkflowHandle

from ...metrics.counters import increase_counter
from ..utils import (
    partialclass,
    pg_query,
    rewrap_exceptions,
)

# Query to create a temporal lookup
create_temporal_lookup_query = parse_one("""
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
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.NoDataFoundError: partialclass(
            HTTPException,
            status_code=404,
            detail="No executions found for the specified task",
        ),
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer or task does not exist",
        ),
    }
)
@pg_query
@increase_counter("create_temporal_lookup")
@beartype
async def create_temporal_lookup(
    *,
    developer_id: UUID,  # TODO: what to do with this parameter?
    execution_id: UUID,
    workflow_handle: WorkflowHandle,
) -> tuple[str, list]:
    """
    Create a temporal lookup for a given execution.

    Parameters:
        developer_id (UUID): The ID of the developer.
        execution_id (UUID): The ID of the execution.
        workflow_handle (WorkflowHandle): The workflow handle.

    Returns:
        tuple[str, list]: SQL query and parameters for creating the temporal lookup.
    """
    developer_id = str(developer_id)
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

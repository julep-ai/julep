from typing import TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError
from temporalio.client import WorkflowHandle

from ...common.utils.cozo import cozo_process_mutate_data
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
)

T = TypeVar("T")


@rewrap_exceptions(
    {
        AssertionError: partialclass(HTTPException, status_code=404),
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@cozo_query
@beartype
def create_temporal_lookup(
    *,
    developer_id: UUID,
    execution_id: UUID,
    workflow_handle: WorkflowHandle,
) -> tuple[list[str], dict]:
    developer_id = str(developer_id)
    execution_id = str(execution_id)

    temporal_columns, temporal_values = cozo_process_mutate_data(
        {
            "execution_id": execution_id,
            "id": workflow_handle.id,
            "run_id": workflow_handle.run_id,
            "first_execution_run_id": workflow_handle.first_execution_run_id,
            "result_run_id": workflow_handle.result_run_id,
        }
    )

    temporal_executions_lookup_query = f"""
    ?[{temporal_columns}] <- $temporal_values

    :insert temporal_executions_lookup {{
        {temporal_columns}
    }}
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id,
            "executions",
            execution_id=execution_id,
            parents=[("agents", "agent_id"), ("tasks", "task_id")],
        ),
        temporal_executions_lookup_query,
    ]

    return (queries, {"temporal_values": temporal_values})

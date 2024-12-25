from typing import Annotated, Any, TypeVar
from uuid import UUID

from beartype import beartype
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateExecutionRequest, Execution
from ...common.utils.datetime import utcnow
from ...common.utils.types import dict_like
from ...metrics.counters import increase_counter
from sqlglot import parse_one
import asyncpg
from fastapi import HTTPException
from ..utils import (
    pg_query,
    wrap_in_class,
    rewrap_exceptions,
    partialclass,
)
from .constants import OUTPUT_UNNEST_KEY


create_execution_query = parse_one("""
INSERT INTO executions
(
    developer_id,
    task_id,
    execution_id,
    input,
    metadata,
    task_version
)
VALUES
(
    $1,
    $2,
    $3,
    $4,
    $5,
    1
)
RETURNING *;
""").sql(pretty=True)


@rewrap_exceptions(
{
    asyncpg.NoDataFoundError: partialclass(
        HTTPException, 
        status_code=404,
        detail="No executions found for the specified task"
    ),
    asyncpg.ForeignKeyViolationError: partialclass(
        HTTPException,
        status_code=404,
        detail="The specified developer or task does not exist"
    ),
}
)
@wrap_in_class(
    Execution,
    one=True,
    transform=lambda d: {
        "id": d["execution_id"],
        "status": "queued",
        "updated_at": utcnow(),
        **d,
    },
)
@pg_query
@increase_counter("create_execution")
@beartype
async def create_execution(
    *,
    developer_id: UUID,
    task_id: UUID,
    execution_id: UUID | None = None,
    data: Annotated[CreateExecutionRequest | dict, dict_like(CreateExecutionRequest)],
) -> tuple[str, list]:
    """
    Create a new execution.

    Parameters:
        developer_id (UUID): The ID of the developer.
        task_id (UUID): The ID of the task.
        execution_id (UUID | None): The ID of the execution.
        data (CreateExecutionRequest | dict): The data for the execution.

    Returns:
        tuple[str, list]: SQL query and parameters for creating the execution.
    """
    execution_id = execution_id or uuid7()

    developer_id = str(developer_id)
    task_id = str(task_id)
    execution_id = str(execution_id)

    if isinstance(data, CreateExecutionRequest):
        data.metadata = data.metadata or {}
        execution_data = data.model_dump()
    else:
        data["metadata"] = data.get("metadata", {})
        execution_data = data

    if execution_data["output"] is not None and not isinstance(
        execution_data["output"], dict
    ):
        execution_data["output"] = {OUTPUT_UNNEST_KEY: execution_data["output"]}

    return (
        create_execution_query,
        [
            developer_id,
            task_id,
            execution_id,
            execution_data["input"],
            execution_data["metadata"],
        ],
    )

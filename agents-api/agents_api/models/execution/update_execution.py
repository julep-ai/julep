from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import (
    ResourceUpdatedResponse,
    UpdateExecutionRequest,
)
from ...common.protocol.tasks import (
    valid_previous_statuses as valid_previous_statuses_map,
)
from ...common.utils.cozo import cozo_process_mutate_data
from ...metrics.counters import increase_counter
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)
from .constants import OUTPUT_UNNEST_KEY

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {"id": d["execution_id"], **d},
    _kind="inserted",
)
@cozo_query
@increase_counter("update_execution")
@beartype
def update_execution(
    *,
    developer_id: UUID,
    task_id: UUID,
    execution_id: UUID,
    data: UpdateExecutionRequest,
    output: dict | Any | None = None,
    error: str | None = None,
) -> tuple[list[str], dict]:
    developer_id = str(developer_id)
    task_id = str(task_id)
    execution_id = str(execution_id)

    valid_previous_statuses: list[str] | None = valid_previous_statuses_map.get(
        data.status, None
    )

    execution_data: dict = data.model_dump(exclude_none=True)

    if output is not None and not isinstance(output, dict):
        output: dict = {OUTPUT_UNNEST_KEY: output}

    columns, values = cozo_process_mutate_data(
        {
            **execution_data,
            "task_id": task_id,
            "execution_id": execution_id,
            "output": output,
            "error": error,
        }
    )

    validate_status_query = """
    valid_status[count(status)] :=
        *executions {
            status,
            execution_id: to_uuid($execution_id),
        }, 
        status in $valid_previous_statuses

    ?[num] :=
        valid_status[num],
        assert(num > 0, 'Invalid status')

    :limit 1
    """

    update_query = f"""
    input[{columns}] <- $values
    ?[{columns}, updated_at] :=
        input[{columns}],
        updated_at = now()

    :update executions {{
        updated_at,
        {columns}
    }}

    :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id,
            "executions",
            execution_id=execution_id,
            parents=[("agents", "agent_id"), ("tasks", "task_id")],
        ),
        validate_status_query if valid_previous_statuses is not None else "",
        update_query,
    ]

    return (
        queries,
        {
            "values": values,
            "valid_previous_statuses": valid_previous_statuses,
            "execution_id": str(execution_id),
        },
    )

from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import (
    ResourceUpdatedResponse,
    UpdateExecutionRequest,
)
from ...common.utils.cozo import cozo_process_mutate_data
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)


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
    transform=lambda d: {"id": d["execution_id"], "jobs": [], **d},
)
@cozo_query
@beartype
def update_execution(
    *,
    developer_id: UUID,
    task_id: UUID,
    execution_id: UUID,
    data: UpdateExecutionRequest,
) -> tuple[str, dict]:
    developer_id = str(developer_id)
    task_id = str(task_id)
    execution_id = str(execution_id)

    valid_previous_statuses = []
    match data.status:
        case "running":
            valid_previous_statuses = ["queued", "starting", "awaiting_input"]
        case "cancelled":
            valid_previous_statuses = [
                "queued",
                "starting",
                "awaiting_input",
                "running",
            ]

    execution_data = data.model_dump(exclude_none=True)

    columns, values = cozo_process_mutate_data(
        {
            **execution_data,
            "task_id": task_id,
            "execution_id": execution_id,
        }
    )

    validate_status_query = """
    ?[status, execution_id] :=
        *executions {
            status,
            execution_id,
        }, status in $valid_previous_statuses

    :assert some
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
            "tasks",
            task_id=task_id,
            parents=[("agents", "agent_id")],
        ),
        validate_status_query,
        update_query,
    ]

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return (
        query,
        {"values": values, "valid_previous_statuses": valid_previous_statuses},
    )

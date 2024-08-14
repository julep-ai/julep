"""
This module contains the functionality for creating a new Task in the 'cozodb` database.
It constructs and executes a datalog query to insert Task data.
"""

from uuid import UUID, uuid4

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import (
    CreateTaskRequest,
)
from ...common.protocol.tasks import spec_to_task, task_to_spec
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
@wrap_in_class(spec_to_task, one=True, _kind="inserted")
@cozo_query
@beartype
def create_task(
    *,
    developer_id: UUID,
    agent_id: UUID,
    task_id: UUID | None = None,
    data: CreateTaskRequest,
) -> tuple[list[str], dict]:
    data.metadata = data.metadata or {}
    data.input_schema = data.input_schema or {}

    task_id = task_id or uuid4()
    task_spec = task_to_spec(data)

    # Prepares the update data by filtering out None values and adding user_id and developer_id.
    columns, values = cozo_process_mutate_data(
        {
            **task_spec.model_dump(exclude_none=True, exclude_unset=True),
            "task_id": str(task_id),
            "agent_id": str(agent_id),
        }
    )

    create_query = f"""
    input[{columns}] <- $values
    ?[{columns}, updated_at_ms, created_at] :=
        input[{columns}],
        updated_at_ms = [floor(now() * 1000), true],
        created_at = now(),

    :insert tasks {{
        {columns},
        updated_at_ms,
        created_at,
    }}

    :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "agents", agent_id=agent_id),
        create_query,
    ]

    return (
        queries,
        {
            "agent_id": str(agent_id),
            "values": values,
        },
    )

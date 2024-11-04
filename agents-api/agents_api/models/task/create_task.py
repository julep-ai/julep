"""
This module contains the functionality for creating a new Task in the 'cozodb` database.
It constructs and executes a datalog query to insert Task data.
"""

from typing import Any, TypeVar
from uuid import UUID, uuid4

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import (
    CreateTaskRequest,
    ResourceCreatedResponse,
)
from ...common.protocol.tasks import task_to_spec
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
    ResourceCreatedResponse,
    one=True,
    transform=lambda d: {
        "id": d["task_id"],
        "jobs": [],
        "created_at": d["created_at"],
        **d,
    },
)
@cozo_query
@increase_counter("create_task")
@beartype
def create_task(
    *,
    developer_id: UUID,
    agent_id: UUID,
    task_id: UUID | None = None,
    data: CreateTaskRequest,
) -> tuple[list[str], dict]:
    """
    Creates a new task.

    Parameters:
        developer_id (UUID): The unique identifier of the developer associated with the task.
        agent_id (UUID): The unique identifier of the agent associated with the task.
        task_id (UUID | None): The unique identifier of the task. If not provided, a new UUID will be generated.
        data (CreateTaskRequest): The data to create the task with.

    Returns:
        ResourceCreatedResponse: The created task.
    """

    data.metadata = data.metadata or {}
    data.input_schema = data.input_schema or {}

    task_id = task_id or uuid4()
    task_spec = task_to_spec(data)

    # Prepares the update data by filtering out None values and adding user_id and developer_id.
    columns, values = cozo_process_mutate_data(
        {
            **task_spec.model_dump(exclude_none=True, exclude_unset=True, mode="json"),
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

"""
This module contains the functionality for creating a new Task in the 'cozodb` database.
It constructs and executes a datalog query to insert Task data.
"""

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import (
    CreateOrUpdateTaskRequest,
    ResourceUpdatedResponse,
)
from ...common.protocol.tasks import task_to_spec
from ...common.utils.cozo import cozo_process_mutate_data
from ...common.utils.datetime import utcnow
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
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {
        "id": d["task_id"],
        "jobs": [],
        "updated_at": d["updated_at_ms"][0] / 1000,
        **d,
    },
)
@cozo_query
@beartype
def create_or_update_task(
    *,
    developer_id: UUID,
    agent_id: UUID,
    task_id: UUID,
    data: CreateOrUpdateTaskRequest,
) -> tuple[list[str], dict]:
    developer_id = str(developer_id)
    agent_id = str(agent_id)
    task_id = str(task_id)

    data.metadata = data.metadata or {}
    data.input_schema = data.input_schema or {}

    task_data = task_to_spec(data).model_dump(
        exclude_none=True, exclude_unset=True, mode="json"
    )
    task_data.pop("task_id", None)
    task_data["created_at"] = utcnow().timestamp()

    columns, values = cozo_process_mutate_data(task_data)

    update_query = f"""
        input[{columns}] <- $values
        ids[agent_id, task_id] :=
            agent_id = to_uuid($agent_id),
            task_id = to_uuid($task_id)

        ?[updated_at_ms, agent_id, task_id, {columns}] :=
            ids[agent_id, task_id],
            input[{columns}],
            updated_at_ms = [floor(now() * 1000), true]

        :put tasks {{
            agent_id,
            task_id,
            updated_at_ms,
            {columns},
        }}

        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "agents", agent_id=agent_id),
        update_query,
    ]

    return (
        queries,
        {
            "values": values,
            "agent_id": agent_id,
            "task_id": task_id,
        },
    )

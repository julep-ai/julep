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

from ...autogen.openapi_model import PatchTaskRequest, ResourceUpdatedResponse, TaskSpec
from ...common.protocol.tasks import task_to_spec
from ...common.utils.cozo import cozo_process_mutate_data
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
    _kind="inserted",
)
@cozo_query
@beartype
def patch_task(
    *,
    developer_id: UUID,
    agent_id: UUID,
    task_id: UUID,
    data: PatchTaskRequest,
) -> tuple[list[str], dict]:
    developer_id = str(developer_id)
    agent_id = str(agent_id)
    task_id = str(task_id)

    data.input_schema = data.input_schema or {}
    task_data = task_to_spec(data, exclude_none=True, exclude_unset=True).model_dump(
        exclude_none=True, exclude_unset=True
    )
    task_data.pop("task_id", None)

    assert len(task_data), "No data provided to update task"
    metadata = task_data.pop("metadata", {})
    columns, values = cozo_process_mutate_data(task_data)

    all_columns = list(TaskSpec.model_fields.keys())
    all_columns.remove("id")
    all_columns.remove("main")

    missing_columns = (
        set(all_columns)
        - set(columns.split(","))
        - {"metadata", "created_at", "updated_at"}
    )
    missing_columns_str = ",".join(missing_columns)

    patch_query = f"""
        input[{columns}] <- $values
        ids[agent_id, task_id] :=
            agent_id = to_uuid($agent_id),
            task_id = to_uuid($task_id)

        original[created_at, metadata, {missing_columns_str}] :=
            ids[agent_id, task_id],
            *tasks{{
                agent_id,
                task_id,
                created_at,
                metadata,
                {missing_columns_str},
            }}

        ?[created_at, updated_at_ms, agent_id, task_id, metadata, {columns}, {missing_columns_str}] :=
            ids[agent_id, task_id],
            input[{columns}],
            original[created_at, _metadata, {missing_columns_str}],
            updated_at_ms = [floor(now() * 1000), true],
            metadata = _metadata ++ $metadata

        :put tasks {{
            agent_id,
            task_id,
            created_at,
            updated_at_ms,
            metadata,
            {columns}, {missing_columns_str}
        }}

        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "agents", agent_id=agent_id),
        patch_query,
    ]

    return (
        queries,
        {
            "values": values,
            "agent_id": agent_id,
            "task_id": task_id,
            "metadata": metadata,
        },
    )

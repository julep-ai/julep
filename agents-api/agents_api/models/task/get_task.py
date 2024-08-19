from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)
from .create_task import spec_to_task

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(spec_to_task, one=True)
@cozo_query
@beartype
def get_task(
    *,
    developer_id: UUID,
    task_id: UUID,
) -> tuple[list[str], dict]:
    get_query = """
    input[task_id] <- [[to_uuid($task_id)]]

    task_data[
        task_id,
        agent_id,
        name,
        description,
        input_schema,
        tools,
        inherit_tools,
        workflows,
        created_at,
        updated_at,
        metadata,
    ] := 
        input[task_id],
        *tasks {
            agent_id,
            task_id,
            updated_at_ms,
            name,
            description,
            input_schema,
            tools,
            inherit_tools,
            workflows,
            created_at,
            metadata,
            @ 'NOW'
        },
        updated_at = to_int(updated_at_ms) / 1000

    tool_data[collect(tool_def)] :=
        task_data[_, agent_id, _, _, _, _, _, _, _, _, _],
        *tools {
            agent_id,
            type,
            name,
            spec,
        }, tool_def = {
            "type": type,
            "name": name,
            "spec": spec,
            "inherited": true,
        }

    ?[
        id,
        agent_id,
        name,
        description,
        input_schema,
        tools,
        inherit_tools,
        workflows,
        created_at,
        updated_at,
        metadata,
    ] := 
        tool_data[inherited_tools],
        task_data[
            id,
            agent_id,
            name,
            description,
            input_schema,
            task_tools,
            inherit_tools,
            workflows,
            created_at,
            updated_at,
            metadata,
        ], tools = task_tools ++ if(inherit_tools, inherited_tools, [])

    :limit 1
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "tasks", task_id=task_id, parents=[("agents", "agent_id")]
        ),
        get_query,
    ]

    return (queries, {"task_id": str(task_id)})

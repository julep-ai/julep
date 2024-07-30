"""
This module contains the functionality for creating a new Task in the 'cozodb` database.
It constructs and executes a datalog query to insert Task data.
"""

import sys
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, TypedDict
else:
    from typing import NotRequired, TypedDict


from beartype import beartype

from ...autogen.openapi_model import CreateTaskRequest, Task, UpdateTaskRequest
from ...common.utils.cozo import cozo_process_mutate_data
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)


class Workflow(TypedDict):
    name: str
    steps: list[dict]


class TaskToolDef(TypedDict):
    type: str
    name: str
    spec: dict
    inherited: NotRequired[bool]


class TaskSpec(TypedDict):
    task_id: NotRequired[str | None]
    name: str
    description: str
    input_schema: dict
    inherit_tools: bool
    tools: NotRequired[list[TaskToolDef]]
    metadata: dict
    workflows: list[Workflow]
    created_at: datetime


# FIXME: resolve this typing issue
# pytype: disable=bad-return-type
def task_to_spec(
    task: Task | CreateTaskRequest | UpdateTaskRequest, **model_opts
) -> TaskSpec:
    task_data = task.model_dump(**model_opts)
    task_id = task_data.pop("id", None)
    workflows = []

    for k in list(task_data.keys()):
        if k in TaskSpec.__annotations__:
            continue

        steps = task_data.pop(k)
        workflows.append(Workflow(name=k, steps=steps))

    tools = task_data.pop("tools", [])
    tools = [TaskToolDef(spec=tool.pop(tool["type"]), **tool) for tool in tools]

    return TaskSpec(
        task_id=task_id,
        workflows=workflows,
        tools=tools,
        **task_data,
    )


# pytype: enable=bad-return-type


def spec_to_task_data(spec: dict) -> dict:
    task_id = spec.pop("task_id", None)

    workflows = spec.pop("workflows")
    workflows_dict = {workflow["name"]: workflow["steps"] for workflow in workflows}

    tools = spec.pop("tools", [])
    tools = [{tool["type"]: tool.pop("spec"), **tool} for tool in tools]

    return {
        "id": task_id,
        "tools": tools,
        **spec,
        **workflows_dict,
    }


def spec_to_task(**spec) -> Task | CreateTaskRequest:
    if not spec.get("id"):
        spec["id"] = spec.pop("task_id", None)

    if not spec.get("updated_at"):
        [updated_at_ms, _] = spec.pop("updated_at_ms", None)
        spec["updated_at"] = updated_at_ms and (updated_at_ms / 1000)

    cls = Task if spec["id"] else CreateTaskRequest
    return cls(**spec_to_task_data(spec))


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
def create_task(
    *,
    developer_id: UUID,
    agent_id: UUID,
    task_id: UUID | None = None,
    data: CreateTaskRequest,
) -> tuple[str, dict]:
    data.metadata = data.metadata or {}
    data.input_schema = data.input_schema or {}

    task_id = task_id or uuid4()
    task_spec = task_to_spec(data)

    # Prepares the update data by filtering out None values and adding user_id and developer_id.
    columns, values = cozo_process_mutate_data(
        {
            **task_spec,
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

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return (
        query,
        {
            "agent_id": str(agent_id),
            "values": values,
        },
    )

from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateTaskRequest, ResourceUpdatedResponse
from ...common.protocol.tasks import task_to_spec
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for creating or updating a task
tools_query = parse_one("""
INSERT INTO tools (
    task_version,
    developer_id,
    agent_id,
    task_id,
    tool_id,
    type,
    name,
    description,
    spec
)
VALUES (
    1, -- task_version
    $1, -- developer_id
    $2, -- agent_id
    $3, -- task_id
    $4, -- tool_id
    $5, -- type
    $6, -- name
    $7, -- description
    $8 -- spec
)
""").sql(pretty=True)

task_query = parse_one("""
INSERT INTO tasks (
    "version",
    developer_id,
    agent_id,
    task_id,
    name,
    description,
    input_schema,
    spec,
    metadata
)
VALUES (
    1, -- version
    $1, -- developer_id
    $2, -- agent_id
    $3, -- task_id
    $4, -- name
    $5, -- description
    $6::jsonb, -- input_schema
    $7::jsonb, -- spec
    $8::jsonb -- metadata
)
RETURNING *
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer or agent does not exist.",
        ),
        asyncpg.UniqueViolationError: partialclass(
            HTTPException,
            status_code=409,
            detail="A task with this ID already exists for this agent.",
        ),
    }
)
@wrap_in_class(
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {
        "id": d["task_id"],
        "jobs": [],
        # "updated_at": d["updated_at"].timestamp(),
        **d,
    },
)
@increase_counter("create_task")
@pg_query
@beartype
async def create_task(
    *, developer_id: UUID, agent_id: UUID, task_id: UUID, data: CreateTaskRequest
) -> list[tuple[str, list, Literal["fetch", "fetchmany"]]]:
    """
    Constructs an SQL query to create or update a task.

    Args:
        developer_id (UUID): The UUID of the developer.
        agent_id (UUID): The UUID of the agent.
        task_id (UUID): The UUID of the task.
        data (CreateTaskRequest): The task data to insert or update.

    Returns:
        tuple[str, list]: SQL query and parameters.

    Raises:
        HTTPException: If developer/agent doesn't exist (404) or on unique constraint violation (409)
    """
    task_data = task_to_spec(data).model_dump(exclude_none=True, mode="json")

    params = [
        developer_id,  # $1
        agent_id,  # $2
        task_id,  # $3
        data.name,  # $4
        data.description,  # $5
        data.input_schema or {},  # $6
        task_data["spec"],  # $7
        data.metadata or {},  # $8
    ]

    tool_params = [
        [
            developer_id,
            agent_id,
            task_id,
            uuid7(),  # tool_id
            tool.type,
            tool.name,
            tool.description,
            getattr(tool, tool.type),  # spec
        ]
        for tool in data.tools or []
    ]

    return [
        (
            task_query,
            params,
            "fetch",
        ),
        (
            tools_query,
            tool_params,
            "fetchmany",
        ),
    ]

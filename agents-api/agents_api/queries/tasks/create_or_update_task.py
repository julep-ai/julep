from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateOrUpdateTaskRequest, ResourceUpdatedResponse
from ...common.protocol.tasks import task_to_spec
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for creating or updating a task
tools_query = parse_one("""
WITH current_version AS (
    SELECT COALESCE(MAX("version"), 0) + 1 as next_version
    FROM tasks 
    WHERE developer_id = $1
      AND task_id = $3
)
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
SELECT
    next_version,       -- task_version
    $1,                 -- developer_id
    $2,                 -- agent_id
    $3,                 -- task_id
    $4,                 -- tool_id
    $5,                 -- type
    $6,                 -- name
    $7,                 -- description
    $8                  -- spec
FROM current_version
""").sql(pretty=True)

task_query = parse_one("""
WITH current_version AS (
    SELECT COALESCE(MAX("version"), 0) + 1 as next_version
    FROM tasks 
    WHERE developer_id = $1
      AND task_id = $4
)
INSERT INTO tasks (
    "version",
    developer_id,
    canonical_name,
    agent_id,
    task_id,
    name,
    description,
    input_schema,
    spec,
    metadata
)
SELECT
    next_version,       -- version
    $1,                 -- developer_id
    $2,                 -- canonical_name
    $3,                 -- agent_id
    $4,                 -- task_id
    $5,                 -- name
    $6,                 -- description
    $7::jsonb,          -- input_schema
    $8::jsonb,          -- spec
    $9::jsonb           -- metadata
FROM current_version
RETURNING *, (SELECT next_version FROM current_version) as next_version
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
        "updated_at": d["updated_at"].timestamp(),
        **d,
    },
)
@increase_counter("create_or_update_task")
@pg_query
@beartype
async def create_or_update_task(
    *,
    developer_id: UUID,
    agent_id: UUID,
    task_id: UUID,
    data: CreateOrUpdateTaskRequest,
) -> list[tuple[str, list, Literal["fetch", "fetchmany"]]]:
    """
    Constructs an SQL query to create or update a task.

    Args:
        developer_id (UUID): The UUID of the developer.
        agent_id (UUID): The UUID of the agent.
        task_id (UUID): The UUID of the task.
        data (CreateOrUpdateTaskRequest): The task data to insert or update.

    Returns:
        list[tuple[str, list, Literal["fetch", "fetchmany"]]]: List of SQL queries and parameters.

    Raises:
        HTTPException: If developer/agent doesn't exist (404) or on unique constraint violation (409)
    """
    task_data = task_to_spec(data).model_dump(exclude_none=True, mode="json")

    # Generate canonical name from task name if not provided
    canonical_name = data.canonical_name or task_data["name"].lower().replace(" ", "_")

    # Version will be determined by the CTE
    task_params = [
        developer_id,  # $1
        canonical_name,  # $2
        agent_id,  # $3
        task_id,  # $4
        task_data["name"],  # $5
        task_data.get("description"),  # $6
        data.input_schema or {},  # $7
        task_data["spec"],  # $8
        data.metadata or {},  # $9
    ]

    queries = [(task_query, task_params, "fetch")]

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

    # Add tools query if there are tools
    if tool_params:
        queries.append((tools_query, tool_params, "fetchmany"))

    return queries

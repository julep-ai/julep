from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import ResourceUpdatedResponse, UpdateTaskRequest
from ...common.protocol.tasks import task_to_spec
from ...common.utils.datetime import utcnow
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Update task query using INSERT with version increment
update_task_query = parse_one("""
WITH current_version AS (
    SELECT MAX("version") as current_version,
           canonical_name as existing_canonical_name
    FROM tasks 
    WHERE developer_id = $1 
      AND task_id = $3
    GROUP BY task_id, canonical_name
    HAVING MAX("version") IS NOT NULL  -- This ensures we only proceed if a version exists
)
INSERT INTO tasks (
    "version",
    developer_id,            -- $1
    canonical_name,          -- $2
    task_id,                 -- $3
    agent_id,                -- $4
    metadata,                -- $5
    name,                    -- $6
    description,             -- $7
    inherit_tools,           -- $8
    input_schema,            -- $9
)
SELECT
    current_version + 1,           -- version
    $1,                           -- developer_id
    COALESCE($2, existing_canonical_name),  -- canonical_name
    $3,                           -- task_id
    $4,                           -- agent_id
    $5::jsonb,                    -- metadata
    $6,                           -- name
    $7,                           -- description
    $8,                           -- inherit_tools
    $9::jsonb                     -- input_schema
FROM current_version
RETURNING *;
""").sql(pretty=True)

# Update workflows query to use UPDATE instead of INSERT
workflows_query = parse_one("""
WITH version AS (
    SELECT COALESCE(MAX(version), 0) as current_version
    FROM tasks 
    WHERE developer_id = $1 AND task_id = $2
)
INSERT INTO workflows (
    developer_id,
    task_id,
    version,
    name,
    step_idx,
    step_type,
    step_definition
)
SELECT
    $1,                 -- developer_id
    $2,                 -- task_id
    current_version,    -- version (from CTE)
    $3,                 -- name
    $4,                 -- step_idx
    $5,                 -- step_type
    $6                  -- step_definition
FROM version
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
        asyncpg.NoDataFoundError: partialclass(
            HTTPException,
            status_code=404,
            detail="Task not found",
        ),
    }
)
@wrap_in_class(
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: 
    {
        "id": d["task_id"], 
        "updated_at": utcnow(),
        "jobs": [],
    },
)
@increase_counter("update_task")
@pg_query(return_index=0)
@beartype
async def update_task(
    *,
    developer_id: UUID,
    task_id: UUID,
    agent_id: UUID,
    data: UpdateTaskRequest,
) -> list[tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]]:
    """
    Updates a task and its associated workflows with version control.

    Parameters:
        developer_id (UUID): The unique identifier of the developer.
        task_id (UUID): The unique identifier of the task to update.
        data (UpdateTaskRequest): The update data.
        agent_id (UUID): The unique identifier of the agent.
    Returns:
        list[tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]]: List of queries to execute.
    """
    # Parameters for updating the task
    update_task_params = [
        developer_id,  # $1
        data.canonical_name,  # $2
        task_id,  # $3
        agent_id,  # $4
        data.metadata or {},  # $5
        data.name,  # $6
        data.description,  # $7
        data.inherit_tools,  # $8
        data.input_schema or {},  # $9
    ]

    # Generate workflows from task data
    workflows_spec = task_to_spec(data).model_dump(mode="json")
    workflow_params = []
    for workflow in workflows_spec.get("workflows", []):
        workflow_name = workflow.get("name")
        steps = workflow.get("steps", [])
        for step_idx, step in enumerate(steps):
            workflow_params.append(
                [
                    developer_id,  # $1
                    task_id,  # $2
                    workflow_name,  # $3
                    step_idx,  # $4
                    step["kind_"],  # $5
                    step[step["kind_"]],  # $6
                ]
            )

    return [
        (
            update_task_query,
            update_task_params,
            "fetchrow",
        ),
        (
            workflows_query,
            workflow_params,
            "fetchmany",
        ),
    ]

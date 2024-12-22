from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateTaskRequest, ResourceCreatedResponse
from ...common.protocol.tasks import task_to_spec
from ...metrics.counters import increase_counter
from ..utils import (
    generate_canonical_name,
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

# Define the raw SQL query for creating or updating a task
tools_query = parse_one("""
INSERT INTO tools (
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
    canonical_name,
    description,
    inherit_tools,
    input_schema,
    metadata
)
VALUES (
    1, -- version
    $1, -- developer_id
    $2, -- agent_id
    $3, -- task_id
    $4, -- name
    $5, -- canonical_name
    $6, -- description
    $7, -- inherit_tools
    $8::jsonb, -- input_schema
    $9::jsonb -- metadata
)
RETURNING *
""").sql(pretty=True)

# Define the raw SQL query for inserting workflows
workflows_query = parse_one("""
INSERT INTO workflows (
    developer_id,
    task_id,
    "version",
    name,
    step_idx,
    step_type,
    step_definition
)
VALUES (
    $1, -- developer_id
    $2, -- task_id
    $3, -- version
    $4, -- name
    $5, -- step_idx
    $6, -- step_type
    $7  -- step_definition
)
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
    ResourceCreatedResponse,
    one=True,
    transform=lambda d: {
        "id": d["task_id"],
        "jobs": [],
        # "updated_at": d["updated_at"].timestamp(),
        **d,
    },
)
@increase_counter("create_task")
@pg_query(return_index=0)
@beartype
async def create_task(
    *,
    developer_id: UUID,
    agent_id: UUID,
    task_id: UUID | None = None,
    data: CreateTaskRequest,
) -> list[tuple[str, list, Literal["fetch", "fetchmany"]]]:
    """
    Constructs SQL queries to create or update a task along with its associated tools and workflows.

    Args:
        developer_id (UUID): The UUID of the developer.
        agent_id (UUID): The UUID of the agent.
        task_id (UUID, optional): The UUID of the task. If not provided, a new UUID is generated.
        data (CreateTaskRequest): The task data to insert or update.

    Returns:
        tuple[str, list]: SQL query and parameters.

    Raises:
        HTTPException: If developer/agent doesn't exist (404) or on unique constraint violation (409)
    """
    task_id = task_id or uuid7()

    # Insert parameters for the tasks table
    task_params = [
        developer_id,  # $1
        agent_id,  # $2
        task_id,  # $3
        data.name,  # $4
        data.canonical_name or generate_canonical_name(),  # $5
        data.description,  # $6
        data.inherit_tools,  # $7
        data.input_schema or {},  # $8
        data.metadata or {},  # $9
    ]

    # Prepare tool parameters for the tools table
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

    # Generate workflows from task data using task_to_spec
    workflows_spec = task_to_spec(data).model_dump(exclude_none=True, mode="json")
    workflow_params = []
    for workflow in workflows_spec.get("workflows", []):
        workflow_name = workflow.get("name")
        steps = workflow.get("steps", [])
        for step_idx, step in enumerate(steps):
            workflow_params.append(
                [
                    developer_id,  # $1
                    task_id,  # $2
                    1,  # $3 (version)
                    workflow_name,  # $4
                    step_idx,  # $5
                    step["kind_"],  # $6
                    step[step["kind_"]],  # $7
                ]
            )

    return [
        (
            task_query,
            task_params,
            "fetch",
        ),
        (
            tools_query,
            tool_params,
            "fetchmany",
        ),
        (
            workflows_query,
            workflow_params,
            "fetchmany",
        ),
    ]

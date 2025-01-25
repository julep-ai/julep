from typing import Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import PatchTaskRequest, ResourceUpdatedResponse
from ...common.protocol.models import task_to_spec
from ...common.utils.datetime import utcnow
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import increase_counter
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Update task query using INSERT with version increment
patch_task_query = """
WITH current_version AS (
    SELECT MAX("version") as current_version,
           canonical_name as existing_canonical_name,
           metadata as existing_metadata,
           name as existing_name,
           description as existing_description,
           inherit_tools as existing_inherit_tools,
           input_schema as existing_input_schema
    FROM tasks
    WHERE developer_id = $1
      AND task_id = $3
    GROUP BY canonical_name, metadata, name, description, inherit_tools, input_schema
    HAVING MAX("version") IS NOT NULL  -- This ensures we only proceed if a version exists
)
INSERT INTO tasks (
    "version",
    developer_id,            -- $1
    canonical_name,          -- $2
    task_id,                -- $3
    agent_id,               -- $4
    metadata,               -- $5
    name,                   -- $6
    description,            -- $7
    inherit_tools,          -- $8
    input_schema           -- $9
)
SELECT
    current_version + 1,                                    -- version
    $1,                                                    -- developer_id
    COALESCE($2, existing_canonical_name),                 -- canonical_name
    $3,                                                    -- task_id
    $4,                                                    -- agent_id
    COALESCE($5::jsonb, existing_metadata),               -- metadata
    COALESCE($6, existing_name),                          -- name
    COALESCE($7, existing_description),                    -- description
    COALESCE($8, existing_inherit_tools),                 -- inherit_tools
    COALESCE($9::jsonb, existing_input_schema)            -- input_schema
FROM current_version
RETURNING *;
"""

# When main is None - just copy existing workflows with new version
copy_workflows_query = """
WITH current_version AS (
    SELECT MAX(version) - 1 as current_version
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
    developer_id,
    task_id,
    (SELECT current_version + 1 FROM current_version),  -- new version
    name,
    step_idx,
    step_type,
    step_definition
FROM workflows
WHERE developer_id = $1
AND task_id = $2
AND version = (SELECT current_version FROM current_version)
"""

# When main is provided - create new workflows (existing query)
new_workflows_query = """
WITH current_version AS (
    SELECT COALESCE(MAX(version), 0) - 1 as next_version
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
    next_version + 1,   -- version
    $3,                 -- name
    $4,                 -- step_idx
    $5,                 -- step_type
    $6                  -- step_definition
FROM current_version
"""


@rewrap_exceptions(common_db_exceptions("task", ["patch"]))
@wrap_in_class(
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {"id": d["task_id"], "updated_at": utcnow()},
)
@increase_counter("patch_task")
@pg_query(return_index=0)
@beartype
async def patch_task(
    *,
    developer_id: UUID,
    task_id: UUID,
    agent_id: UUID,
    data: PatchTaskRequest,
) -> list[tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]]:
    """
    Updates a task and its associated workflows with version control.
    Only updates the fields that are provided in the request.

    Parameters:
        developer_id (UUID): The unique identifier of the developer.
        task_id (UUID): The unique identifier of the task to update.
        data (PatchTaskRequest): The partial update data.
        agent_id (UUID): The unique identifier of the agent.
    Returns:
        list[tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]]: List of queries to execute.
    """
    # Parameters for patching the task

    patch_task_params = [
        developer_id,  # $1
        data.canonical_name,  # $2
        task_id,  # $3
        agent_id,  # $4
        data.metadata or None,  # $5
        data.name or None,  # $6
        data.description or None,  # $7
        data.inherit_tools,  # $8
        data.input_schema,  # $9
    ]

    if data.main is None:
        workflow_query = copy_workflows_query
        workflow_params = [[developer_id, task_id]]  # Only need these params
    else:
        workflow_query = new_workflows_query
        workflow_params = []
        workflows_spec = task_to_spec(data).model_dump(mode="json")
        for workflow in workflows_spec.get("workflows", []):
            workflow_name = workflow.get("name")
            steps = workflow.get("steps", [])
            for step_idx, step in enumerate(steps):
                workflow_params.append([
                    developer_id,  # $1
                    task_id,  # $2
                    workflow_name,  # $3
                    step_idx,  # $4
                    step["kind_"],  # $5
                    step,  # $6
                ])

    return [
        (
            patch_task_query,
            patch_task_params,
            "fetchrow",
        ),
        (
            workflow_query,
            workflow_params,
            "fetchmany",
        ),
    ]

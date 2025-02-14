from typing import Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import UpdateTaskRequest
from ...common.protocol.models import spec_to_task, task_to_spec
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class
from .get_task import get_task_query

# Update task query using INSERT with version increment
update_task_query = """
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
    input_schema             -- $9
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
"""

# Update workflows query to use UPDATE instead of INSERT
workflows_query = """
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
FROM version;
"""


@rewrap_exceptions(common_db_exceptions("task", ["update"]))
@wrap_in_class(
    spec_to_task,
    one=True,
)
@query_metrics("update_task")
@pg_query
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
            update_task_query,
            update_task_params,
            "fetchrow",
        ),
        (
            workflows_query,
            workflow_params,
            "fetchmany",
        ),
        (
            get_task_query,
            [developer_id, task_id],
            "fetchrow",
        ),
    ]

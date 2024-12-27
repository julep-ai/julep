from typing import Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for deleting workflows
workflow_query = """
DELETE FROM workflows
WHERE developer_id = $1 AND task_id = $2;
"""

# Define the raw SQL query for deleting tasks
task_query = """
DELETE FROM tasks
WHERE developer_id = $1 AND task_id = $2
RETURNING task_id;
"""


@rewrap_exceptions(common_db_exceptions("task", ["delete"]))
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": d["task_id"],
        "deleted_at": utcnow(),
    },
)
@pg_query
@beartype
async def delete_task(
    *,
    developer_id: UUID,
    task_id: UUID,
) -> list[tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]]:
    """
    Deletes a task by its unique identifier along with its associated workflows.

    Parameters:
        developer_id (UUID): The unique identifier of the developer associated with the task.
        task_id (UUID): The unique identifier of the task to delete.

    Returns:
        tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]: SQL query, parameters, and fetch method.

    Raises:
        HTTPException: If developer/agent doesn't exist (404) or on unique constraint violation (409)
    """

    return [
        (workflow_query, [developer_id, task_id], "fetch"),
        (task_query, [developer_id, task_id], "fetchrow"),
    ]

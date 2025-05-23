from typing import Literal
from uuid import UUID

from beartype import beartype

from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Query to count executions for a given task
execution_count_query = """
SELECT COUNT(*) FROM latest_executions
WHERE
    developer_id = $1
    AND created_at >= (select created_at from developers where developer_id = $1 LIMIT 1)
    AND task_id = $2;
"""


@rewrap_exceptions(common_db_exceptions("execution", ["count"]))
@wrap_in_class(dict, one=True)
@pg_query
@beartype
async def count_executions(
    *,
    developer_id: UUID,
    task_id: UUID,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    """
    Count the number of executions for a given task.

    Parameters:
        developer_id (UUID): The ID of the developer.
        task_id (UUID): The ID of the task.

    Returns:
        tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]: SQL query and parameters for counting executions.
    """
    return (
        execution_count_query,
        [developer_id, task_id],
        "fetchrow",
    )

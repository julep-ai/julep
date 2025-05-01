"""Query functions for counting execution transitions."""

from typing import Literal
from uuid import UUID

from beartype import beartype

from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
count_transitions_by_developer_query = """
SELECT COUNT(*)
FROM transitions t
JOIN executions e ON t.execution_id = e.execution_id
WHERE e.developer_id = $1;
"""


@rewrap_exceptions(common_db_exceptions("transition", ["count"]))
@wrap_in_class(dict, one=True)
@query_metrics("count_transitions")
@pg_query
@beartype
async def count_transitions(
    *,
    developer_id: UUID,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    """
    Counts transitions from an execution or all transitions from a developer.

    Args:
        execution_id (UUID, optional): The execution ID to count transitions for.
        developer_id (UUID, optional): The developer ID to count all transitions for.

    Returns:
        tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]: SQL query, parameters,
        and fetch method.

    Notes:
        - Either execution_id or developer_id must be provided.
        - If both are provided, execution_id takes precedence.
    """
    return (
        count_transitions_by_developer_query,
        [developer_id],
        "fetchrow",
    )

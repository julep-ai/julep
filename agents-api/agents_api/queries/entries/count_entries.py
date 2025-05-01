"""Query functions for counting session entries."""

from uuid import UUID

from beartype import beartype

from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
count_entries_by_developer_query = """
SELECT COUNT(*)
FROM entries e
JOIN sessions s ON e.session_id = s.session_id
WHERE s.developer_id = $1;
"""


@rewrap_exceptions(common_db_exceptions("entry", ["count"]))
@wrap_in_class(dict, one=True)
@query_metrics("count_entries")
@pg_query
@beartype
async def count_entries(
    *,
    developer_id: UUID,
) -> tuple[str, list]:
    """
    Counts entries from a session or all entries from a developer.

    Args:
        session_id (UUID, optional): The session ID to count entries for.
        developer_id (UUID, optional): The developer ID to count all entries for.

    Returns:
        tuple[str, list]: SQL query and parameters.

    Notes:
        - Either session_id or developer_id must be provided.
        - If both are provided, session_id takes precedence.
    """
    return (
        count_entries_by_developer_query,
        [developer_id],
    )

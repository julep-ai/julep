"""
This module contains functionality for creating usage records in the PostgreSQL database.
It tracks token usage and costs for LLM API calls.
"""

from typing import Literal
from uuid import UUID

from beartype import beartype

from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

usage_query = """
SELECT developer_id, active, tags, monthly_cost AS cost, bucket_start AS month
FROM developer_cost_monthly
WHERE developer_id = $1
ORDER BY month DESC
LIMIT 1;
"""


@rewrap_exceptions(common_db_exceptions("usage", ["get"]))
@wrap_in_class(
    dict,
    one=True,
)
@query_metrics("get_user_cost")
@pg_query
@beartype
async def get_user_cost(
    *,
    developer_id: UUID,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    """
    Get the cost of a user's usage.

    Parameters:
        developer_id (UUID): The unique identifier for the developer.

    Returns:
        tuple[str, list]: SQL query and parameters for creating the usage record.
    """

    return (
        usage_query,
        [
            developer_id,
        ],
        "fetchrow",
    )

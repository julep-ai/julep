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
SELECT
    COALESCE(developer_id, $1) as developer_id,
    COALESCE(active, TRUE) as active,
    COALESCE(tags, '{}') as tags,
    COALESCE(monthly_cost, 0.0) AS cost,
    COALESCE(bucket_start, NOW()) AS month
FROM (
    SELECT developer_id, active, tags, monthly_cost, bucket_start
    FROM developer_cost_monthly
    WHERE developer_id = $1
    ORDER BY bucket_start DESC
    LIMIT 1
) as subq
UNION ALL
SELECT
    $1 as developer_id,
    TRUE as active,
    '{}' as tags,
    0.0 AS cost,
    NOW() AS month
WHERE NOT EXISTS (
    SELECT 1
    FROM developer_cost_monthly
    WHERE developer_id = $1
)
LIMIT 1;
"""


@rewrap_exceptions(common_db_exceptions("usage", ["get"]))
@wrap_in_class(
    dict,
    one=True,
)
@query_metrics("get_usage_cost")
@pg_query
@beartype
async def get_usage_cost(
    *,
    developer_id: UUID,
) -> tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]:
    """
    Get the cost of a developer's usage.

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

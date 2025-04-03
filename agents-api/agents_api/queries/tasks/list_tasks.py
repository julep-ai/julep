from typing import Annotated, Any, Literal
from uuid import UUID

from beartype import beartype
from beartype.vale import Is

from ...common.protocol.models import spec_to_task
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import make_num_validator, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for listing tasks
list_tasks_query = """
SELECT
    t.*,
    COALESCE(
        jsonb_agg(
            CASE WHEN w.name IS NOT NULL THEN
                jsonb_build_object(
                    'name', w.name,
                    'steps', jsonb_build_array(w.step_definition)
                )
            END
        ) FILTER (WHERE w.name IS NOT NULL),
        '[]'::jsonb
    ) as workflows
FROM
    tasks t
LEFT JOIN
    workflows w ON t.developer_id = w.developer_id AND t.task_id = w.task_id AND t.version = w.version
WHERE
    t.developer_id = $1
    AND t.agent_id = $2
    {metadata_filter_query}
GROUP BY t.developer_id, t.task_id, t.canonical_name, t.agent_id, t.version
ORDER BY
    CASE WHEN $5 = 'created_at' AND $6 = 'asc' THEN t.created_at END ASC NULLS LAST,
    CASE WHEN $5 = 'created_at' AND $6 = 'desc' THEN t.created_at END DESC NULLS LAST,
    CASE WHEN $5 = 'updated_at' AND $6 = 'asc' THEN t.updated_at END ASC NULLS LAST,
    CASE WHEN $5 = 'updated_at' AND $6 = 'desc' THEN t.updated_at END DESC NULLS LAST
LIMIT $3 OFFSET $4;
"""


@rewrap_exceptions(common_db_exceptions("task", ["list"]))
@wrap_in_class(spec_to_task)
@pg_query
@beartype
async def list_tasks(
    *,
    developer_id: UUID,
    agent_id: UUID,
    limit: Annotated[
        int,
        Is[
            make_num_validator(
                min_value=1, max_value=100, err_msg="Limit must be between 1 and 100"
            )
        ],
    ] = 100,
    offset: Annotated[
        int, Is[make_num_validator(min_value=0, err_msg="Offset must be >= 0")]
    ] = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict[str, Any] = {},
) -> tuple[str, list]:
    """
    Retrieves all tasks for a given developer with pagination and sorting.

    Parameters:
        developer_id (UUID): The unique identifier of the developer.
        agent_id (UUID): The unique identifier of the agent.
        limit (int): Maximum number of records to return (default: 100)
        offset (int): Number of records to skip (default: 0)
        sort_by (str): Field to sort by ("created_at" or "updated_at")
        direction (str): Sort direction ("asc" or "desc")
        metadata_filter (dict): Optional metadata filters

    Returns:
        tuple[str, list]: SQL query and parameters.

    Raises:
        HTTPException: If parameters are invalid or developer/agent doesn't exist
    """
    # if direction.lower() not in ["asc", "desc"]:
    #     raise HTTPException(status_code=400, detail="Invalid sort direction")

    # Format query with metadata filter if needed
    query = list_tasks_query.format(
        metadata_filter_query="AND metadata @> $7::jsonb" if metadata_filter else "",
    )

    # Build parameters list
    params = [
        developer_id,
        agent_id,
        limit,
        offset,
        sort_by,
        direction,
    ]

    if metadata_filter:
        params.append(metadata_filter)

    return (query, params)

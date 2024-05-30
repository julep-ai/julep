from typing import Any
from uuid import UUID

from ...common.utils import json
from ..utils import cozo_query


@cozo_query
def list_tasks_query(
    agent_id: UUID,
    limit: int = 100,
    offset: int = 0,
    # metadata_filter: dict[str, Any] = {},
) -> tuple[str, dict]:
    """Lists tasks from the 'cozodb' database based on the provided filters.

    Parameters:
        developer_id (UUID): The developer's ID to filter tasks by.
        limit (int): The maximum number of tasks to return.
        offset (int): The offset from which to start listing tasks.
    Returns:
        pd.DataFrame: A DataFrame containing the queried task data.
    """

    query = """
    ?[
        task_id,
        name,
        description,
        input_schema,
        tools_available,
        workflows,
        created_at,
        updated_at,
    ] := *tasks {
            agent_id: to_uuid($agent_id),
            task_id,
            updated_at_ms,
            name,
            description,
            input_schema,
            tools_available,
            workflows,
            created_at,
            @ 'NOW'
        }, updated_at = to_int(updated_at_ms) / 1000

      :limit $limit
      :offset $offset
    """

    return (query, {"agent_id": str(agent_id), "limit": limit, "offset": offset})

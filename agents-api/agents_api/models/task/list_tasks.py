from typing import Any
from uuid import UUID

from ...common.utils import json
from ..utils import cozo_query


@cozo_query
def list_tasks_query(
    developer_id: UUID,
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
    pass

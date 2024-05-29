from typing import Literal
from uuid import UUID

from ..utils import cozo_query


@cozo_query
def get_execution_status_query(task_id: UUID, developer_id: UUID) -> tuple[str, dict]:
    task_id = str(task_id)
    developer_id = str(developer_id)
    query = """"""
    return (query, {"task_id": task_id, "developer_id": developer_id})

from uuid import UUID

from ..utils import cozo_query


@cozo_query
def get_task_query(developer_id: UUID, task_id: UUID) -> tuple[str, dict]:
    query = """"""
    return (query, {"developer_id": str(developer_id), "task_id": str(task_id)})

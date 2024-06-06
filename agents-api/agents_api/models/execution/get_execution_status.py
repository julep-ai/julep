from uuid import UUID
from beartype import beartype

from ..utils import cozo_query


@cozo_query
@beartype
def get_execution_status_query(task_id: UUID, execution_id: UUID) -> tuple[str, dict]:
    task_id = str(task_id)
    execution_id = str(execution_id)
    query = """
{
    ?[status] := *executions {
        task_id: to_uuid($task_id),
        execution_id: to_uuid($execution_id),
        status,
    }
}
"""
    return (query, {"task_id": task_id, "execution_id": execution_id})

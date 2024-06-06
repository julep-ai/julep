from uuid import UUID

from ..utils import cozo_query

from beartype import beartype


@cozo_query
@beartype
def get_execution_query(
    task_id: UUID,
    execution_id: UUID,
) -> tuple[str, dict]:
    query = """
{
    ?[status, arguments, created_at, updated_at] := *executions {
        task_id: to_uuid($task_id),
        execution_id: to_uuid($execution_id),
        status,
        arguments,
        created_at,
        updated_at,
    }
}
"""
    return (
        query,
        {
            "task_id": str(task_id),
            "execution_id": str(execution_id),
        },
    )

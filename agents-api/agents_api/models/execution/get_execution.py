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
    input[task_id, execution_id] <- [[to_uuid($task_id), to_uuid($execution_id)]]

    ?[id, task_id, status, arguments, session_id, created_at, updated_at] := 
        input[task_id, execution_id],
        *executions {
            task_id,
            execution_id,
            status,
            arguments,
            session_id,
            created_at,
            updated_at,
        },
        id = execution_id
}
"""
    return (
        query,
        {
            "task_id": str(task_id),
            "execution_id": str(execution_id),
        },
    )

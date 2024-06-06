from uuid import UUID

from beartype import beartype

from ..utils import cozo_query


@cozo_query
@beartype
def list_task_executions_query(
    agent_id: UUID, task_id: UUID, developer_id: UUID
) -> tuple[str, dict]:
    # TODO: Check for agent in developer ID; Assert whether dev can access agent and by relation the task
    query = """
{
    ?[
        execution_id,
        status,
        arguments,
        created_at,
        updated_at,
    ] := *executions {
            task_id: to_uuid($task_id),
            execution_id,
            status,
            arguments,
            created_at,
            updated_at,
        }
        :limit 10
        :offset 0

}
"""
    return (query, {"task_id": str(task_id)})

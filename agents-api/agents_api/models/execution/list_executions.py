from uuid import UUID

from beartype import beartype

from ..utils import cozo_query


@cozo_query
@beartype
def list_task_executions_query(
    agent_id: UUID, task_id: UUID, developer_id: UUID, limit: int = 100, offset: int = 0
) -> tuple[str, dict]:
    # TODO: Check for agent in developer ID; Assert whether dev can access agent and by relation the task
    query = f"""
{{
    ?[
        execution_id,
        status,
        arguments,
        session_id,
        created_at,
        updated_at,
    ] := *executions {{
            task_id: to_uuid($task_id),
            execution_id,
            status,
            arguments,
            session_id,
            created_at,
            updated_at,
        }}
        :limit {limit}
        :offset {offset}

}}
"""
    return (query, {"task_id": str(task_id)})

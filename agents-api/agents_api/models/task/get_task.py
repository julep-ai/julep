from uuid import UUID

from ..utils import cozo_query


@cozo_query
def get_task_query(agent_id: UUID, task_id: UUID) -> tuple[str, dict]:
    query = """
    ?[
        name,
        description,
        input_schema,
        tools_available,
        workflows,
        created_at,
        updated_at,
    ] := *tasks {
            agent_id: to_uuid($agent_id),
            task_id: to_uuid($task_id),
            updated_at_ms,
            name,
            description,
            input_schema,
            tools_available,
            workflows,
            created_at,
            @ 'NOW'
        }, updated_at = to_int(updated_at_ms) / 1000
    """

    return (query, {"agent_id": str(agent_id), "task_id": str(task_id)})

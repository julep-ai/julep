from uuid import UUID

from beartype import beartype

from ..utils import cozo_query


@cozo_query
@beartype
def get_task_query(
    agent_id: UUID, task_id: UUID, developer_id: UUID
) -> tuple[str, dict]:
    # TODO: Check for agent in developer ID; Assert whether dev can access agent and by relation the task
    query = """
    ?[
        id,
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
        },
        updated_at = to_int(updated_at_ms) / 1000,
        id = to_uuid($task_id),
    """

    return (query, {"agent_id": str(agent_id), "task_id": str(task_id)})

from uuid import UUID

from beartype import beartype

from ..utils import cozo_query


@cozo_query
@beartype
def list_tasks_query(
    developer_id: UUID,
    agent_id: UUID,
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
    # TODO: Accepts developer ID. Checks if the developer can get this agent, by relation can get the tasks. Assert that the agent exists under the developer.
    query = """
    input[agent_id] <- [[to_uuid($agent_id)]]

    ?[
        id,
        agent_id,
        name,
        description,
        input_schema,
        tools_available,
        workflows,
        created_at,
        updated_at,
    ] := input[agent_id], 
        *tasks {
            agent_id,
            task_id: id,
            updated_at_ms,
            name,
            description,
            input_schema,
            tools_available,
            workflows,
            created_at,
            @ 'NOW'
        }, updated_at = to_int(updated_at_ms) / 1000

      :limit $limit
      :offset $offset
    """

    return (query, {"agent_id": str(agent_id), "limit": limit, "offset": offset})

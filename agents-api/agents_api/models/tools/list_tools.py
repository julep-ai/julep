from uuid import UUID


from ..utils import cozo_query


@cozo_query
def list_functions_by_agent_query(
    agent_id: UUID,
    limit: int = 100,
    offset: int = 0,
) -> tuple[str, dict]:
    agent_id = str(agent_id)

    query = """
    {
        input[agent_id] <- [[to_uuid($agent_id)]]

        ?[
            agent_id,
            tool_id,
            name,
            description,
            parameters,
            updated_at,
            created_at,
        ] := input[agent_id],
            *agent_functions {
                agent_id,
                tool_id,
                name,
                description,
                parameters,
                updated_at,
                created_at,
            }

        :limit $limit
        :offset $offset
    }"""

    return (query, {"agent_id": agent_id, "limit": limit, "offset": offset})

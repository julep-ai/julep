from uuid import UUID


from ..utils import cozo_query


@cozo_query
def get_function_by_id_query(
    agent_id: UUID,
    tool_id: UUID,
) -> tuple[str, dict]:
    agent_id = str(agent_id)
    tool_id = str(tool_id)

    query = """
    {
        input[agent_id, tool_id] <- [[to_uuid($agent_id), to_uuid($tool_id)]]

        ?[
            agent_id,
            tool_id,
            name,
            description,
            parameters,
            updated_at,
            created_at,
        ] := input[agent_id, tool_id],
            *agent_functions {
                agent_id,
                tool_id,
                name,
                description,
                parameters,
                updated_at,
                created_at,
            }
    }"""

    return (query, {"agent_id": agent_id, "tool_id": tool_id})

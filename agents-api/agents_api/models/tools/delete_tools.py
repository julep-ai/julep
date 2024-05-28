from uuid import UUID

from beartype import beartype


from ..utils import cozo_query


@cozo_query
@beartype
def delete_function_by_id_query(
    agent_id: UUID,
    tool_id: UUID,
) -> tuple[str, dict]:
    agent_id = str(agent_id)
    tool_id = str(tool_id)

    query = """
    {
        # Delete function
        ?[tool_id, agent_id] <- [[
            to_uuid($tool_id),
            to_uuid($agent_id),
        ]]

        :delete agent_functions {
            tool_id,
            agent_id,
        }
        :returning
    }"""

    return (query, {"tool_id": tool_id, "agent_id": agent_id})

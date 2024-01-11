from typing import Literal
from uuid import UUID


def get_function_by_id_query(
    agent_id: UUID,
    tool_id: UUID,
):
    agent_id = str(agent_id)
    tool_id = str(tool_id)

    return f"""
    {{
        input[agent_id, tool_id] <- [[to_uuid("{agent_id}"), to_uuid("{tool_id}")]]

        ?[
            agent_id,
            tool_id,
            name,
            description,
            parameters,
            updated_at,
            created_at,
        ] := input[agent_id, tool_id],
            *agent_functions {{
                agent_id,
                tool_id,
                name,
                description,
                parameters,
                updated_at,
                created_at,
            }}
    }}"""

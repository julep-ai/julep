from typing import Literal
from uuid import UUID


def list_functions_by_agent_query(
    agent_id: UUID,
):
    agent_id = str(agent_id)

    return f"""
    {{
        input[agent_id] <- [[to_uuid("{agent_id}")]]

        ?[
            agent_id,
            tool_id,
            name,
            description,
            parameters,
            updated_at,
            created_at,
        ] := input[agent_id],
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

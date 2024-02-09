from uuid import UUID


def delete_function_by_id_query(agent_id: UUID, tool_id: UUID):
    agent_id = str(agent_id)
    tool_id = str(tool_id)

    return f"""
    {{
        # Delete function
        ?[tool_id, agent_id] <- [[
            to_uuid("{tool_id}"),
            to_uuid("{agent_id}"),
        ]]

        :delete agent_functions {{
            tool_id,
            agent_id,
        }}
        :returning
    }}"""

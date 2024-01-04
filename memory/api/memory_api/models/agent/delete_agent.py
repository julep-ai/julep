from uuid import UUID


def delete_agent_query(agent_id: UUID):
    return f"""
    {{
        # Delete default agent settings
        ?[agent_id] <- [["{agent_id}"]]

        :delete agent_default_settings {{
            agent_id
        }}
    }} {{
        # Delete the agent
        ?[agent_id] <- [["{agent_id}"]]

        :delete agents {{
            agent_id
        }}
    }}"""

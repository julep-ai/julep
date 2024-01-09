from uuid import UUID


def delete_agent_query(developer_id: UUID, agent_id: UUID):
    return f"""
    {{
        # Delete default agent settings
        ?[agent_id] <- [["{agent_id}"]]

        :delete agent_default_settings {{
            agent_id
        }}
    }} {{
        # Delete the agent
        ?[agent_id, developer_id] <- [["{agent_id}", "{developer_id}"]]

        :delete agents {{
            developer_id,
            agent_id
        }}
    }}"""

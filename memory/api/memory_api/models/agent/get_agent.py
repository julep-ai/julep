from uuid import UUID


def get_agent_query(agent_id: UUID):
    return f"""
        input[agent_id] <- [[to_uuid("{agent_id}")]]

        ?[
            agent_id,
            name,
            about,
            created_at,
        ] := input[agent_id],
            *agents {{
                agent_id,
                name,
                about,
                created_at,
            }}"""

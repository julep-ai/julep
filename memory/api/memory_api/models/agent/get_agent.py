get_agent_query = """
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

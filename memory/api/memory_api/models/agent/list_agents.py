list_agents_query = """
    ?[
        agent_id,
        name,
        about,
        created_at,
    ] := *agents {{
            agent_id,
            name,
            about,
            created_at,
        }}
    
    :limit {limit}
    :offset {offset}"""

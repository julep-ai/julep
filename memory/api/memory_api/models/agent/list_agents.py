def list_agents_query(limit: int = 100, offset: int = 0):
    return f"""
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

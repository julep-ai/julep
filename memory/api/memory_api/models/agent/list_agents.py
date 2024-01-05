def list_agents_query(limit: int = 100, offset: int = 0):
    return f"""
        ?[
            id,
            model,
            name,
            about,
            created_at,
            updated_at,
        ] := *agents {{
                agent_id: id,
                model,
                name,
                about,
                created_at,
                updated_at,
            }}
        
        :limit {limit}
        :offset {offset}
        :sort -created_at
    """

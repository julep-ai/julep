create_agent_query = """
    ?[agent_id, name, about, created_at] <- [
        ["{agent_id}", "{name}", "{about}", now()]
    ]
    
    :put agents {{
        agent_id =>
        name,
        about,
        created_at,
    }}"""

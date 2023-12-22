create_agent_query = """
    ?[character_id, name, about, metadata] <- [
        ["{agent_id}", "{name}", "{about}", {{}}]
    ]
    
    :put agents {{
        agent_id =>
        name,
        about,
        metadata,
    }}"""
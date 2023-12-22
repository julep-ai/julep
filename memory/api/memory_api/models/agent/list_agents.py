list_agents_query = """
    ?[
        agent_id,
        name,
        about,
        metadata,
        updated_at,
        created_at,
    ] := *agents {{
            agent_id,
            name,
            about,
            metadata,
            updated_at: validity,
            created_at,
            @ "NOW"
        }}, updated_at = to_int(validity)
    
    :limit {limit}
    :offset {offset}"""
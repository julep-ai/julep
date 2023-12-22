get_agent_query = """
    input[character_id] <- [[to_uuid("{agent_id}")]]

    ?[
        character_id,
        name,
        about,
        metadata,
        updated_at,
        created_at,
    ] := input[character_id],
        *agents {{
            character_id,
            name,
            about,
            metadata,
            updated_at: validity,
            created_at,
            @ "NOW"
        }}, updated_at = to_int(validity)"""
get_user_query = """
    input[user_id] <- [[to_uuid("{id}")]]

    ?[
        user_id,
        name,
        email,
        about,
        metadata,
        updated_at,
        created_at,
    ] := input[user_id],
        *users {{
            user_id,
            name,
            email,
            about,
            metadata,
            updated_at: validity,
            created_at,
            @ "NOW"
        }}, updated_at = to_int(validity)"""

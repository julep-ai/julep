list_users_query = """
    ?[
        user_id,
        name,
        email,
        about,
        metadata,
        updated_at,
        created_at,
    ] := *users {{
            user_id,
            name,
            email,
            about,
            metadata,
            updated_at: validity,
            created_at,
            @ "NOW"
        }}, updated_at = to_int(validity)
    
    :limit {limit}
    :offset {offset}"""
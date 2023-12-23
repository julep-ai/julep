def get_user_query(id):
    return f"""
    input[user_id] <- [[to_uuid("{id}")]]

    ?[
        user_id,
        name,
        about,
        created_at,
    ] := input[user_id],
        *users {{
            user_id,
            name,
            about,
            created_at,
        }}"""

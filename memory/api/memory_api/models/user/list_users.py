def list_users_query(limit, offset):
    return f"""
    ?[
        user_id,
        name,
        about,
        created_at,
    ] := *users {{
            user_id,
            name,
            about,
            created_at,
        }}
    
    :limit {limit}
    :offset {offset}"""

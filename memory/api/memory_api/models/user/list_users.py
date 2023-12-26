def list_users_query(limit: int = 100, offset: int = 0):
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

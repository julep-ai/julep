def list_users_query(limit: int = 100, offset: int = 0):
    return f"""
    ?[
        id,
        name,
        about,
        created_at,
        updated_at,
    ] := *users {{
            user_id: id,
            name,
            about,
            created_at,
            updated_at,
        }}
    
    :limit {limit}
    :offset {offset}
    :sort -created_at
    """

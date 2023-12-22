create_user_query = """
    ?[user_id, name, about, created_at] <- [
        ["{user_id}", "{name}", "{about}", now()]
    ]
    
    :put users {{
        user_id =>
        name,
        about,
        created_at,
    }}"""

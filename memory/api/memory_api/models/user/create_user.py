create_user_query = """
    ?[user_id, name, email, about, metadata] <- [
        ["{user_id}", "{name}", "{email}", "{about}", {{}}]
    ]
    
    :put users {{
        user_id =>
        name,
        email,
        about,
        metadata,
    }}"""
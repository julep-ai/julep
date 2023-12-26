from uuid import UUID


def create_user_query(user_id: UUID, name: str, about: str):
    user_id = str(user_id)

    return f"""
    ?[user_id, name, about, created_at] <- [
        ["{user_id}", "{name}", "{about}", now()]
    ]
    
    :put users {{
        user_id =>
        name,
        about,
        created_at,
    }}"""

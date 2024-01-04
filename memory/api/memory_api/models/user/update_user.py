from uuid import UUID


def update_user_query(user_id: UUID, name: str, about: str):
    user_id = str(user_id)

    return f"""
        # update the user
        ?[user_id, name, about, updated_at] <- [
            [to_uuid("{user_id}"), "{name}", "{about}", now()]
        ]

        :update users {{
            user_id =>
            name,
            about,
            updated_at,
        }}
        :returning
    """

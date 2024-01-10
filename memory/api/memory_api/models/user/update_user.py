from uuid import UUID


def update_user_query(developer_id: UUID, user_id: UUID, name: str, about: str):
    user_id = str(user_id)

    return f"""
        # update the user
        ?[developer_id, user_id, name, about, updated_at] <- [
            [to_uuid("{developer_id}"), to_uuid("{user_id}"), "{name}", "{about}", now()]
        ]

        :update users {{
            developer_id,
            user_id =>
            name,
            about,
            updated_at,
        }}
        :returning
    """

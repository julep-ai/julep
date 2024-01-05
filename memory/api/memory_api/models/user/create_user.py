from uuid import UUID


def create_user_query(user_id: UUID, name: str, about: str):
    user_id = str(user_id)

    return f"""
        # Then create the user
        ?[user_id, name, about] <- [
            ["{user_id}", "{name}", "{about}"]
        ]

        :insert users {{
            user_id =>
            name,
            about,
        }}
        :returning
    """

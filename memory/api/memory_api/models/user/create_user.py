from uuid import UUID


def create_user_query(user_id: UUID, name: str, about: str):
    user_id = str(user_id)

    return f"""
    {{
        # First ensure that the user does not already exist
        input[user_id] <- [[to_uuid("{user_id}")]]

        ?[
            user_id,
            name,
            about,
            created_at,
            updated_at,
        ] :=
            input[user_id],
            *users{{
                user_id,
                name,
                about,
                created_at,
                updated_at,
            }}

        :ensure_not users {{
            user_id =>
            name,
            about,
            created_at,
            updated_at,
        }}
    }}
    {{
        # Then create the user
        ?[user_id, name, about, created_at, updated_at] <- [
            ["{user_id}", "{name}", "{about}", now(), now()]
        ]

        :put users {{
            user_id =>
            name,
            about,
            created_at,
            updated_at,
        }}
    }}"""

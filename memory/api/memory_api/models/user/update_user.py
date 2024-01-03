from uuid import UUID


def update_user_query(user_id: UUID, name: str, about: str):
    user_id = str(user_id)

    return f"""
    {{
        # First ensure that the user does already exist
        input[user_id] <- [[to_uuid("{user_id}")]]

        search[collect(user_id)] :=
            input[user_id],
            *users{{
                user_id,
            }}

        ?[found] :=
            search[found],
            assert(length(found) == 1, 'user_id not found')

    }} {{
        # Then update the user
        input[user_id, name, about, updated_at] <- [
            [to_uuid("{user_id}"), "{name}", "{about}", now()]
        ]

        ?[user_id, name, about, created_at, updated_at] :=
            input[user_id, name, about, updated_at],
            *users{{user_id, created_at}},

        :put users {{
            user_id =>
            name,
            about,
            created_at,
            updated_at,
        }}
    }}"""

from uuid import UUID


def get_user_query(developer_id: UUID, user_id: UUID):
    user_id = str(user_id)
    developer_id = str(developer_id)

    return f"""
    input[developer_id, user_id] <- [[to_uuid("{developer_id}"), to_uuid("{user_id}")]]

    ?[
        id,
        name,
        about,
        created_at,
        updated_at,
        metadata,
    ] := input[developer_id, id],
        *users {{
            user_id: id,
            developer_id,
            name,
            about,
            created_at,
            updated_at,
            metadata,
        }}"""

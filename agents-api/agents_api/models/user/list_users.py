from uuid import UUID


def list_users_query(developer_id: UUID, limit: int = 100, offset: int = 0):
    return f"""
    input[developer_id] <- [[to_uuid("{developer_id}")]]

    ?[
        id,
        name,
        about,
        created_at,
        updated_at,
        metadata,
    ] :=
        input[developer_id], 
        *users {{
            user_id: id,
            developer_id,
            name,
            about,
            created_at,
            updated_at,
            metadata,
        }}
    
    :limit {limit}
    :offset {offset}
    :sort -created_at
    """

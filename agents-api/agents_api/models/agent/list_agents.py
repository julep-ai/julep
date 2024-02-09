from uuid import UUID


def list_agents_query(developer_id: UUID, limit: int = 100, offset: int = 0):
    return f"""
    {{
        input[developer_id] <- [[to_uuid("{developer_id}")]]

        ?[
            id,
            model,
            name,
            about,
            created_at,
            updated_at,
        ] := input[developer_id],
            *agents {{
                developer_id,
                agent_id: id,
                model,
                name,
                about,
                created_at,
                updated_at,
            }}
        
        :limit {limit}
        :offset {offset}
        :sort -created_at
    }}"""

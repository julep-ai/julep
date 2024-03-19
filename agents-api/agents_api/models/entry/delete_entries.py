from uuid import UUID


def delete_entries_query(session_id: UUID):
    return f"""
    {{
        input[session_id] <- [[
            to_uuid("{session_id}"),
        ]]

        ?[
            session_id,
            entry_id,
            role,
            name,
            content,
            source,
            token_count,
            created_at,
            timestamp,
        ] := input[session_id],
            *entries{{
                session_id,
                entry_id,
                role,
                name,
                content,
                source,
                token_count,
                created_at,
                timestamp,
            }}
        
        :delete entries {{
            session_id,
            entry_id,
            role,
            name,
            content,
            source,
            token_count,
            created_at,
            timestamp,
        }}
    }}"""

from uuid import UUID


def get_entries_query(session_id: UUID, limit: int = 100, offset: int = 0):
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
            }},
            source == "api_request" || source == "api_response",

        :sort created_at
        :limit {limit}
        :offset {offset}
    }}"""

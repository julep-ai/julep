get_entries_query = """
    input[session_id] <- [[
        to_uuid("{session_id}"),
    ]]

    ?[
        session_id,
        entry_id,
        role,
        name,
        content,
        token_count,
    ] := input[session_id],
        *entries{{
            session_id,
            entry_id,
            role,
            name,
            content,
            token_count,
        }}"""

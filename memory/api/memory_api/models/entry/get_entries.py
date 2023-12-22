get_entries_query = """
    input[session_id] <- [[
        to_uuid("{session_id}"),
    ]]

    ?[
        session_id,
        entry_id,
        timestamp,
        role,
        name,
        content,
        token_count,
        processed,
        parent_id,
    ] := input[session_id],
        *entries{{
            session_id,
            entry_id,
            timestamp,
            role,
            name,
            content,
            token_count,
            processed,
            parent_id,
        }}"""
get_session_query = """
        input[session_id] <- [[
        to_uuid("{session_id}"),
    ]]

    ?[
        character_id,
        user_id,
        session_id,
        updated_at,
        situation,
        summary,
        metadata,
        created_at,
    ] := input[session_id],
        *sessions{{
            character_id,
            user_id,
            session_id,
            situation,
            summary,
            metadata,
            updated_at: validity,
            created_at,
            @ "NOW"
        }}, updated_at = to_int(validity)"""
list_sessions_query = """
    ?[
        agent_id,
        user_id,
        session_id,
        updated_at,
        situation,
        summary,
        metadata,
        created_at,
    ] := *sessions{{
        agent_id,
        user_id,
        session_id,
        situation,
        summary,
        metadata,
        updated_at: validity,
        created_at,
        @ "NOW"
    }}

    :limit {limit}
    :offset {offset}"""
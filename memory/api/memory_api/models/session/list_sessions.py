list_sessions_query = """
    ?[
        agent_id,
        user_id,
        session_id,
        situation,
        summary,
        updated_at,
        created_at,
    ] :=
        *sessions{{
            session_id,
            situation,
            summary,
            created_at,
            updated_at: validity,
            @ "NOW"
        }},
        *session_lookup{{
            agent_id,
            user_id,
            session_id,
        }}, updated_at = to_int(validity)"""

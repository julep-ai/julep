def create_session_query(id, agent_id, user_id, situation):
    return f"""
{{
    # Create a new session
    input[session_id, agent_id, user_id, situation] <- [[
        to_uuid("{id}"),
        to_uuid("{agent_id}"),
        to_uuid("{user_id}"),
        "{situation}",
    ]]

    ?[session_id, situation, summary, created_at] := input[
        session_id,
        _,
        _,
        situation,
    ], summary = null, created_at = now()

    :put sessions {{
        session_id,
        situation,
        summary,
        created_at,
    }}
}}
{{
    # Create a new session lookup
    input[session_id, agent_id, user_id, situation] <- [[
        to_uuid("{id}"),
        to_uuid("{agent_id}"),
        to_uuid("{user_id}"),
        "{situation}",
    ]]

    ?[agent_id, user_id, session_id] := input[
        session_id,
        agent_id,
        user_id,
        _,
    ]

    :put session_lookup {{
        agent_id,
        user_id,
        session_id,
    }}
}}"""

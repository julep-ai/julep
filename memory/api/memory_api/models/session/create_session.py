from uuid import UUID


def create_session_query(
    session_id: UUID, agent_id: UUID, user_id: UUID, situation: str
):
    session_id = str(session_id)
    agent_id = str(agent_id)
    user_id = str(user_id)

    return f"""
{{
    # Create a new session
    input[session_id, agent_id, user_id, situation] <- [[
        to_uuid("{session_id}"),
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
        to_uuid("{session_id}"),
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

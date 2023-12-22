create_session_query = """
        ?[session_id, agent_id, user_id, situation, metadata] <- [[
        to_uuid("{id}"),
        to_uuid("{agent_id}"),
        to_uuid("{user_id}"),
        "{situation}",
        {{}},
    ]]

    :put sessions {{
        agent_id,
        user_id,
        session_id,
        situation,
        metadata,
    }}"""
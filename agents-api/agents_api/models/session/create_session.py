from uuid import UUID


def create_session_query(
    session_id: UUID,
    developer_id: UUID,
    agent_id: UUID,
    user_id: UUID,
    situation: str | None,
    metadata: dict = {},
):
    session_id = str(session_id)
    agent_id = str(agent_id)
    user_id = str(user_id)
    developer_id = str(developer_id)
    situation = situation or ""

    return f"""
    {{
        # Create a new session lookup
        ?[session_id, agent_id, user_id] <- [[
            to_uuid("{session_id}"),
            to_uuid("{agent_id}"),
            to_uuid("{user_id}"),
        ]]

        :insert session_lookup {{
            agent_id,
            user_id,
            session_id,
        }}
    }} {{
        # Create a new session
        ?[session_id, developer_id, situation, metadata] <- [[
            to_uuid("{session_id}"),
            to_uuid("{developer_id}"),
            "{situation}",
            {metadata},
        ]]

        :insert sessions {{
            developer_id,
            session_id,
            situation,
            metadata,
        }}
        :returning
     }}"""

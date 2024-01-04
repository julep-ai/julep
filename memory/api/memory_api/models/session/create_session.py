from uuid import UUID


def create_session_query(
    session_id: UUID, agent_id: UUID, user_id: UUID, situation: str
):
    session_id = str(session_id)
    agent_id = str(agent_id)
    user_id = str(user_id)

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
        ?[session_id, situation] <- [[
            to_uuid("{session_id}"),
            "{situation}",
        ]]

        :insert sessions {{
            session_id,
            situation,
        }}
        :returning
     }}"""

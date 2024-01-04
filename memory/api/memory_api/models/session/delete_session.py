from uuid import UUID


def delete_session_query(session_id: UUID):
    session_id = str(session_id)

    return f"""
    {{
        input[session_id] <- [[
            to_uuid("{session_id}"),
        ]]

        ?[
            agent_id,
            user_id,
            session_id,
        ] :=
            input[session_id],
            *session_lookup{{
                agent_id,
                user_id,
                session_id,
            }}

        :delete session_lookup {{
            agent_id,
            user_id,
            session_id,
        }}
    }} {{
        ?[session_id] <- [[
            to_uuid("{session_id}"),
        ]]

        :delete sessions {{
            session_id,
        }}
    }}
    """

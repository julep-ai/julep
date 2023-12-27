from uuid import UUID

from ...clients.cozo import client
from ...common.protocol.sessions import SessionData

def session_data_query(session_id: UUID):
    session_id = str(session_id)

    return f"""
    input[session_id] <- [[
        to_uuid("{session_id}"),
    ]]

    ?[
        agent_id,
        user_id,
        session_id,
        situation,
        summary,
        updated_at,
        created_at,
        user_about,
        agent_about,
    ] := input[session_id],
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
        }}, updated_at = to_int(validity),
        *users{{
            user_id,
            about: user_about,
        }},
        *agents{{
            agent_id,
            about: agent_about,
        }}
    """

def get_session_data(session_id: UUID, client=client) -> SessionData | None:

    query = session_data_query(session_id)
    result = client.run(query)
    if result.empty:
        return None

    data = result.iloc[0].to_dict()

    return SessionData(**data)

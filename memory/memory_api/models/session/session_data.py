from uuid import UUID

from ...clients.cozo import client
from ...common.protocol.sessions import SessionData


def session_data_query(developer_id: UUID, session_id: UUID):
    session_id = str(session_id)

    return f"""
    input[developer_id, session_id] <- [[
        to_uuid("{developer_id}"),
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
        model,
        default_settings,
    ] := input[developer_id, session_id],
        *sessions{{
            developer_id,
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
            model,
        }},
        *agent_default_settings {{
            agent_id,
            frequency_penalty,
            presence_penalty,
            length_penalty,
            repetition_penalty,
            top_p,
            temperature,
        }},
        default_settings = {{
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "length_penalty": length_penalty,
            "repetition_penalty": repetition_penalty,
            "top_p": top_p,
            "temperature": temperature,
        }}
    """


def get_session_data(
    developer_id: UUID, session_id: UUID, client=client
) -> SessionData | None:
    query = session_data_query(developer_id, session_id)
    result = client.run(query)
    if result.empty:
        return None

    data = result.iloc[0].to_dict()

    return SessionData(**data)

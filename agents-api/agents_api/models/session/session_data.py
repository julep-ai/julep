from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client
from ...common.protocol.sessions import SessionData


def session_data_query(
    developer_id: UUID,
    session_id: UUID,
    client: CozoClient = client,
) -> pd.DataFrame:
    query = """
    input[developer_id, session_id] <- [[
        to_uuid($developer_id),
        to_uuid($session_id),
    ]]

    ?[
        agent_id,
        user_id,
        session_id,
        situation,
        summary,
        updated_at,
        created_at,
        user_name,
        user_about,
        agent_name,
        agent_about,
        model,
        default_settings,
        session_metadata,
        users_metadata,
        agents_metadata,
    ] := input[developer_id, session_id],
        *sessions{
            developer_id,
            session_id,
            situation,
            summary,
            created_at,
            updated_at: validity,
            metadata: session_metadata,
            @ "NOW"
        },
        *session_lookup{
            agent_id,
            user_id,
            session_id,
        }, updated_at = to_int(validity),
        *users{
            user_id,
            name: user_name,
            about: user_about,
            metadata: users_metadata,
        },
        *agents{
            agent_id,
            name: agent_name,
            about: agent_about,
            model,
            metadata: agents_metadata,
        },
        *agent_default_settings {
            agent_id,
            frequency_penalty,
            presence_penalty,
            length_penalty,
            repetition_penalty,
            top_p,
            temperature,
            min_p,
            preset,
        },
        default_settings = {
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty,
            "length_penalty": length_penalty,
            "repetition_penalty": repetition_penalty,
            "top_p": top_p,
            "temperature": temperature,
            "min_p": min_p,
            "preset": preset,
        }
    """

    return client.run(query, {"developer_id": str(developer_id), "session_id": str(session_id)})


def get_session_data(
    developer_id: UUID, session_id: UUID, client: CozoClient = client
) -> SessionData | None:
    result = session_data_query(developer_id, session_id, client=client)
    if result.empty:
        return None

    data = result.iloc[0].to_dict()

    return SessionData(**data)

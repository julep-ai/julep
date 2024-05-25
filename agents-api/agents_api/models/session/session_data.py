from uuid import UUID

from pycozo.client import Client as CozoClient

from ...clients.cozo import client as cozo_client
from ...common.protocol.sessions import SessionData
from ..utils import cozo_query


@cozo_query
def session_data_query(
    developer_id: UUID,
    session_id: UUID,
) -> tuple[str, dict]:
    """Constructs and executes a datalog query to retrieve session data from the 'cozodb' database.

    Parameters:
        developer_id (UUID): The developer's unique identifier.
        session_id (UUID): The session's unique identifier.

    Returns:
        pd.DataFrame: A DataFrame containing the query results.
    """
    # This query retrieves detailed session information, including metadata and default settings for agents involved in the session.
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
        metadata,
        render_templates,
        user_metadata,
        agent_metadata,
    ] := input[developer_id, session_id],
        *sessions{
            developer_id,
            session_id,
            situation,
            summary,
            created_at,
            updated_at: validity,
            metadata,
            render_templates,
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
            metadata: user_metadata,
        },
        *agents{
            agent_id,
            name: agent_name,
            about: agent_about,
            model,
            metadata: agent_metadata,
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
        metadata,
        render_templates,
        user_metadata,
        agent_metadata,
    ] := input[developer_id, session_id],
        *sessions{
            developer_id,
            session_id,
            situation,
            summary,
            created_at,
            updated_at: validity,
            metadata,
            render_templates,
            @ "NOW"
        },
        *session_lookup{
            agent_id,
            user_id,
            session_id,
        }, updated_at = to_int(validity),
        not *users{
            user_id
        }, user_name=null, user_about=null, user_metadata=null,
        *agents{
            agent_id,
            name: agent_name,
            about: agent_about,
            model,
            metadata: agent_metadata,
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

    return (query, {"developer_id": str(developer_id), "session_id": str(session_id)})


def get_session_data(
    developer_id: UUID, session_id: UUID, client: CozoClient = cozo_client
) -> SessionData | None:
    """Calls `session_data_query` to get session data and processes the result.

    If data is found, returns a `SessionData` object; otherwise, returns `None`.

    Parameters:
        developer_id (UUID): The developer's unique identifier.
        session_id (UUID): The session's unique identifier.
        client (CozoClient): The database client used to execute the query.

    Returns:
        SessionData | None: A SessionData object if data is found, otherwise `None`.
    """
    result = session_data_query(developer_id, session_id, client=client)
    # Check if the query returned any data; return `None` if not.
    if result.empty:
        return None

    data = result.iloc[0].to_dict()

    return SessionData(**data)

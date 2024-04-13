"""This module contains the implementation for deleting sessions from the 'cozodb' database using datalog queries."""

from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


def delete_session_query(
    developer_id: UUID,
    session_id: UUID,
    client: CozoClient = client,
) -> pd.DataFrame:
    """
    Deletes a session and its related data from the 'cozodb' database.

    Parameters:
    - developer_id (UUID): The unique identifier for the developer.
    - session_id (UUID): The unique identifier for the session to be deleted.
    - client (CozoClient): The database client used to execute the query.

    Returns:
    - pd.DataFrame: A DataFrame containing the result of the deletion query.
    """
    session_id = str(session_id)
    developer_id = str(developer_id)

    # Constructs and executes a datalog query to delete the specified session and its associated data based on the session_id and developer_id.
    query = """
    {
        input[session_id] <- [[
            to_uuid($session_id),
        ]]

        ?[
            agent_id,
            user_id,
            session_id,
        ] :=
            input[session_id],
            *session_lookup{
                agent_id,
                user_id,
                session_id,
            }

        :delete session_lookup {
            agent_id,
            user_id,
            session_id,
        }
    } {
        input[developer_id, session_id] <- [[
            to_uuid($developer_id),
            to_uuid($session_id),
        ]]

        ?[developer_id, session_id, updated_at] :=
            input[developer_id, session_id],
            *sessions {
                developer_id, 
                session_id,
                updated_at,
            }

        :delete sessions {
            developer_id,
            session_id,
            updated_at,
        }
    }
    """

    return client.run(query, {"session_id": session_id, "developer_id": developer_id})

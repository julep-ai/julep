from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


def get_session_query(
    developer_id: UUID,
    session_id: UUID,
    client: CozoClient = client,
) -> pd.DataFrame:
    """
    Constructs and executes a datalog query to retrieve session information from the 'cozodb' database.

    Parameters:
        developer_id (UUID): The developer's unique identifier.
        session_id (UUID): The session's unique identifier.
        client (CozoClient): Allows specifying a custom CozoClient instance for the database connection.

    Returns:
        pd.DataFrame: The result of the query as a pandas DataFrame.
    """
    session_id = str(session_id)
    developer_id = str(developer_id)

    # This query retrieves session information by using `input` to pass parameters,
    # projects specific fields from the `sessions` and `session_lookup` relations,
    # and converts `updated_at` to an integer for easier handling.
    query = """
    input[developer_id, session_id] <- [[
        to_uuid($developer_id),
        to_uuid($session_id),
    ]]

    ?[
        agent_id,
        user_id,
        id,
        situation,
        summary,
        updated_at,
        created_at,
        metadata,
    ] := input[developer_id, id],
        *sessions{
            developer_id,
            session_id: id,
            situation,
            summary,
            created_at,
            updated_at: validity,
            metadata,
            @ "NOW"
        },
        *session_lookup{
            agent_id,
            user_id,
            session_id: id,
        }, updated_at = to_int(validity)"""

    return client.run(query, {"session_id": session_id, "developer_id": developer_id})

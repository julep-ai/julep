"""
This module contains the functionality for creating a new session in the 'cozodb' database.
It constructs and executes a datalog query to insert session data.
"""

from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


"""
Constructs and executes a datalog query to create a new session in the database.

Parameters:
- session_id (UUID): The unique identifier for the session.
- developer_id (UUID): The unique identifier for the developer.
- agent_id (UUID): The unique identifier for the agent.
- user_id (UUID | None): The unique identifier for the user, if applicable.
- situation (str | None): The situation/context of the session.
- metadata (dict): Additional metadata for the session.
- client (CozoClient): The database client used to execute the query.

Returns:
- pd.DataFrame: The result of the query execution.
"""


def create_session_query(
    session_id: UUID,
    developer_id: UUID,
    agent_id: UUID,
    user_id: UUID | None,
    situation: str | None,
    metadata: dict = {},
    client: CozoClient = client,
) -> pd.DataFrame:
    situation: str = situation or ""

    # Construct the datalog query for creating a new session and its lookup.
    query = """
    {
        # This section creates a new session lookup to ensure uniqueness and manage session metadata.
        ?[session_id, agent_id, user_id] <- [[
            $session_id,
            $agent_id,
            $user_id,
        ]]

        :insert session_lookup {
            agent_id,
            user_id,
            session_id,
        }
    } {
        # Insert the new session data into the 'session' table with the specified columns.
        ?[session_id, developer_id, situation, metadata] <- [[
            $session_id,
            $developer_id,
            $situation,
            $metadata,
        ]]

        :insert sessions {
            developer_id,
            session_id,
            situation,
            metadata,
        }
        # Specify the data to return after the query execution, typically the newly created session's ID.
        :returning
     }"""

    # Execute the constructed query with the provided parameters and return the result.
    return client.run(
        query,
        {
            "session_id": str(session_id),
            "agent_id": str(agent_id),
            "user_id": str(user_id) if user_id else None,
            "developer_id": str(developer_id),
            "situation": situation,
            "metadata": metadata,
        },
    )

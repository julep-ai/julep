"""
This module contains the functionality for creating a new session in the 'cozodb' database.
It constructs and executes a datalog query to insert session data.
"""

from beartype import beartype

from uuid import UUID


from ..utils import cozo_query


@cozo_query
@beartype
def create_session_query(
    session_id: UUID,
    developer_id: UUID,
    agent_id: UUID,
    user_id: UUID | None,
    situation: str | None,
    metadata: dict = {},
    render_templates: bool = False,
) -> tuple[str, dict]:
    """
    Constructs and executes a datalog query to create a new session in the database.

    Parameters:
    - session_id (UUID): The unique identifier for the session.
    - developer_id (UUID): The unique identifier for the developer.
    - agent_id (UUID): The unique identifier for the agent.
    - user_id (UUID | None): The unique identifier for the user, if applicable.
    - situation (str | None): The situation/context of the session.
    - metadata (dict): Additional metadata for the session.
    - render_templates (bool): Specifies whether to render templates.

    Returns:
    - pd.DataFrame: The result of the query execution.
    """

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
        ?[session_id, developer_id, situation, metadata, render_templates] <- [[
            $session_id,
            $developer_id,
            $situation,
            $metadata,
            $render_templates,
        ]]

        :insert sessions {
            developer_id,
            session_id,
            situation,
            metadata,
            render_templates,
        }
        # Specify the data to return after the query execution, typically the newly created session's ID.
        :returning
     }"""

    # Execute the constructed query with the provided parameters and return the result.
    return (
        query,
        {
            "session_id": str(session_id),
            "agent_id": str(agent_id),
            "user_id": str(user_id) if user_id else None,
            "developer_id": str(developer_id),
            "situation": situation,
            "metadata": metadata,
            "render_templates": render_templates,
        },
    )

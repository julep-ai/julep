"""
This module contains the implementation of the delete_agent_query function, which is responsible for deleting an agent and its related default settings from the CozoDB database.
"""

from uuid import UUID


from ..utils import cozo_query

"""
Constructs and returns a datalog query for deleting an agent and its default settings from the database.

Parameters:
- developer_id (UUID): The UUID of the developer owning the agent.
- agent_id (UUID): The UUID of the agent to be deleted.
- client (CozoClient, optional): An instance of the CozoClient to execute the query.

Returns:
- tuple[str, dict]: A DataFrame containing the results of the deletion query.
"""


@cozo_query
def delete_agent_query(developer_id: UUID, agent_id: UUID) -> tuple[str, dict]:
    query = """
    {
        # Delete default agent settings
        ?[agent_id] <- [[$agent_id]]

        :delete agent_default_settings {
            agent_id
        }
    } {
        # Delete the agent
        ?[agent_id, developer_id] <- [[$agent_id, $developer_id]]

        :delete agents {
            developer_id,
            agent_id
        }
    }"""

    return (query, {"agent_id": str(agent_id), "developer_id": str(developer_id)})

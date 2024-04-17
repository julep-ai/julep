from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


def get_agent_query(
    developer_id: UUID, agent_id: UUID, client: CozoClient = client
) -> pd.DataFrame:
    """
    Fetches agent details and default settings from the database.

    This function constructs and executes a datalog query to retrieve information about a specific agent, including its default settings, based on the provided agent_id and developer_id.

    Parameters:
    - developer_id (UUID): The unique identifier for the developer.
    - agent_id (UUID): The unique identifier for the agent.
    - client (CozoClient, optional): The database client used to execute the query.

    Returns:
    - pd.DataFrame: A DataFrame containing the agent details and default settings.
    """
    # Constructing a datalog query to retrieve agent details and default settings.
    # The query uses input parameters for agent_id and developer_id to filter the results.
    # It joins the 'agents' and 'agent_default_settings' relations to fetch comprehensive details.
    query = """
    {
        input[agent_id, developer_id] <- [[to_uuid($agent_id), to_uuid($developer_id)]]

        ?[
            id,
            model,
            name,
            about,
            created_at,
            updated_at,
            metadata,
            default_settings,
            instructions,
        ] := input[id, developer_id],
            *agents {
                developer_id,
                agent_id: id,
                model,
                name,
                about,
                created_at,
                updated_at,
                metadata,
                instructions,
            },
            *agent_default_settings {
                agent_id: id,
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
    }
    """

    # Execute the constructed datalog query using the provided CozoClient.
    # The result is returned as a pandas DataFrame.
    return client.run(
        query, {"agent_id": str(agent_id), "developer_id": str(developer_id)}
    )

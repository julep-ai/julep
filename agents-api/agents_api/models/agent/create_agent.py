"""
This module contains the functionality for creating agents in the CozoDB database.
It includes functions to construct and execute datalog queries for inserting new agent records.
"""

from uuid import UUID


from ...common.utils.cozo import cozo_process_mutate_data
from ..utils import cozo_query


@cozo_query
def create_agent_query(
    agent_id: UUID,
    developer_id: UUID,
    name: str,
    about: str,
    model: str,
    instructions: list[str] = [],
    metadata: dict = {},
    default_settings: dict = {},
) -> tuple[str, dict]:
    """
    Constructs and executes a datalog query to create a new agent in the database.

    Parameters:
    - agent_id (UUID): The unique identifier for the agent.
    - developer_id (UUID): The unique identifier for the developer creating the agent.
    - name (str): The name of the agent.
    - about (str): A description of the agent.
    - instructions (list[str], optional): A list of instructions for using the agent. Defaults to an empty list.
    - model (str, optional): The model identifier for the agent. Defaults to "julep-ai/samantha-1-turbo".
    - metadata (dict, optional): A dictionary of metadata for the agent. Defaults to an empty dict.
    - default_settings (dict, optional): A dictionary of default settings for the agent. Defaults to an empty dict.
    - client (CozoClient, optional): The CozoDB client instance to use for the query. Defaults to a preconfigured client instance.

    Returns:
    pd.DataFrame: A DataFrame containing the results of the query execution.
    """

    preset = default_settings.get("preset")
    default_settings["preset"] = getattr(preset, "value", preset)

    settings_cols, settings_vals = cozo_process_mutate_data(
        {
            **default_settings,
            "agent_id": str(agent_id),
        }
    )

    # Create default agent settings
    # Construct a query to insert default settings for the new agent
    default_settings_query = f"""
        ?[{settings_cols}] <- $settings_vals

        :insert agent_default_settings {{
            {settings_cols}
        }}
    """
    # create the agent
    # Construct a query to insert the new agent record into the agents table
    agent_query = """
        ?[agent_id, developer_id, model, name, about, metadata, instructions] <- [
            [$agent_id, $developer_id, $model, $name, $about, $metadata, $instructions]
        ]

        :insert agents {
            developer_id,
            agent_id =>
            model,
            name,
            about,
            metadata,
            instructions,
        }
        :returning
    """

    queries = [
        default_settings_query,
        agent_query,
    ]

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return (
        query,
        {
            "settings_vals": settings_vals,
            "agent_id": str(agent_id),
            "developer_id": str(developer_id),
            "model": model,
            "name": name,
            "about": about,
            "metadata": metadata,
            "instructions": instructions,
        },
    )

"""
This module provides functionality for updating agent data in the 'cozodb' database.
It includes the `update_agent_query` function which constructs and executes datalog queries for updating agent and their settings.
"""

from uuid import UUID


from ...common.utils.cozo import cozo_process_mutate_data
from ..utils import cozo_query


@cozo_query
def update_agent_query(
    agent_id: UUID,
    developer_id: UUID,
    default_settings: dict = {},
    **update_data,
) -> tuple[str, dict]:
    """
    Constructs and executes a datalog query to update an agent and its default settings in the 'cozodb' database.

    Parameters:
    - agent_id (UUID): The unique identifier of the agent to be updated.
    - developer_id (UUID): The unique identifier of the developer associated with the agent.
    - default_settings (dict, optional): A dictionary of default settings to be updated for the agent. Defaults to an empty dict.
    - client (CozoClient, optional): The database client used to execute the query. Defaults to a pre-configured client instance.
    - **update_data: Variable keyword arguments representing additional agent data to be updated.

    Returns:
    - pd.DataFrame: A DataFrame containing the result of the update operation.
    """

    agent_id = str(agent_id)
    developer_id = str(developer_id)
    update_data["instructions"] = update_data.get("instructions", [])

    # Assertion query to check if the agent exists
    assertion_query = """
        ?[developer_id, agent_id] :=
            *agents {
                developer_id,
                agent_id,
            },
            developer_id = to_uuid($developer_id),
            agent_id = to_uuid($agent_id),
        # Assertion to ensure the agent exists before updating.
        :assert some
    """

    # Construct the agent update part of the query with dynamic columns and values based on `update_data`.
    # Agent update query
    agent_update_cols, agent_update_vals = cozo_process_mutate_data(
        {
            **{k: v for k, v in update_data.items() if v is not None},
            "agent_id": agent_id,
            "developer_id": developer_id,
        }
    )

    agent_update_query = f"""
    {{
        # update the agent
        input[{agent_update_cols}] <- $agent_update_vals
        original[created_at] := *agents{{
            developer_id: to_uuid($developer_id),
            agent_id: to_uuid($agent_id),
            created_at,
        }},

        ?[created_at, updated_at, {agent_update_cols}] :=
            input[{agent_update_cols}],
            original[created_at],
            updated_at = now(),

        :put agents {{
            created_at,
            updated_at,
            {agent_update_cols}
        }}
        :returning
    }}
    """

    # Construct the settings update part of the query if `default_settings` are provided.
    # Settings update query
    settings_cols, settings_vals = cozo_process_mutate_data(
        {
            **default_settings,
            "agent_id": agent_id,
        }
    )

    settings_update_query = f"""
    {{
        # update the agent settings
        ?[{settings_cols}] <- $settings_vals

        :put agent_default_settings {{
            {settings_cols}
        }}
    }}
    """

    # Combine agent and settings update queries into a single query string.
    # Combine the queries
    queries = [agent_update_query]

    if len(default_settings) != 0:
        queries.insert(0, settings_update_query)

    # Combine the assertion query with the update queries
    combined_query = "{" + assertion_query + "} " + "\n".join(queries)

    return (
        combined_query,
        {
            "agent_update_vals": agent_update_vals,
            "settings_vals": settings_vals,
            "agent_id": agent_id,
            "developer_id": developer_id,
        },
    )

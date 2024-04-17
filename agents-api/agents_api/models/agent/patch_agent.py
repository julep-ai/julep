from uuid import UUID

import pandas as pd

from ...clients.cozo import client
from ...common.utils.cozo import cozo_process_mutate_data
from ...common.utils.datetime import utcnow


def patch_agent_query(
    agent_id: UUID,
    developer_id: UUID,
    default_settings: dict = {},
    **update_data,
) -> pd.DataFrame:
    """Patches agent data based on provided updates.

    Parameters:
    agent_id (UUID): The unique identifier for the agent.
    developer_id (UUID): The unique identifier for the developer.
    default_settings (dict, optional): Default settings to apply to the agent.
    **update_data: Arbitrary keyword arguments representing data to update.

    Returns:
    pd.DataFrame: The result of the query execution.
    """
    # Construct the query for updating agent information in the database.
    # Agent update query
    metadata = update_data.pop("metadata", {}) or {}
    agent_update_cols, agent_update_vals = cozo_process_mutate_data(
        {
            **{k: v for k, v in update_data.items() if v is not None},
            "agent_id": str(agent_id),
            "developer_id": str(developer_id),
            "updated_at": utcnow().timestamp(),
        }
    )

    agent_update_query = f"""
    {{
        # update the agent
        input[{agent_update_cols}] <- $agent_update_vals

        ?[{agent_update_cols}, metadata] := 
            input[{agent_update_cols}],
            *agents {{
                agent_id: to_uuid($agent_id),
                metadata: md,
            }},
            metadata = concat(md, $metadata)

        :update agents {{
            {agent_update_cols}, metadata,
        }}
        :returning
    }}
    """

    # Construct the query for updating agent's default settings in the database.
    # Settings update query
    settings_cols, settings_vals = cozo_process_mutate_data(
        {
            **default_settings,
            "agent_id": str(agent_id),
        }
    )

    settings_update_query = f"""
    {{
        # update the agent settings
        ?[{settings_cols}] <- $settings_vals

        :update agent_default_settings {{
            {settings_cols}
        }}
    }}
    """

    # Combine agent and settings update queries if default settings are provided.
    # Combine the queries
    queries = [agent_update_query]

    if len(default_settings) != 0:
        queries.insert(0, settings_update_query)

    combined_query = "\n".join(queries)

    return client.run(
        combined_query,
        {
            "agent_update_vals": agent_update_vals,
            "settings_vals": settings_vals,
            "metadata": metadata,
            "agent_id": str(agent_id),
        },
    )

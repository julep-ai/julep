from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client
from ...common.utils import json
from ...common.utils.cozo import cozo_process_mutate_data


def update_agent_query(
    agent_id: UUID,
    developer_id: UUID,
    default_settings: dict = {},
    client: CozoClient = client,
    **update_data,
) -> pd.DataFrame:
    update_data["instructions"] = update_data.get("instructions", [])

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
        input[{agent_update_cols}] <- {json.dumps(agent_update_vals)}
        original[created_at] := *agents{{
            developer_id: to_uuid("{developer_id}"),
            agent_id: to_uuid("{agent_id}"),
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
        ?[{settings_cols}] <- {json.dumps(settings_vals)}

        :put agent_default_settings {{
            {settings_cols}
        }}
    }}
    """

    # Combine the queries
    queries = [agent_update_query]

    if len(default_settings) != 0:
        queries.insert(0, settings_update_query)

    combined_query = "\n".join(queries)

    return client.run(combined_query)

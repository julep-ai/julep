import json
from uuid import UUID

from ...common.utils.cozo import cozo_process_mutate_data
from ...common.utils.datetime import utcnow


def update_agent_query(
    agent_id: UUID,
    developer_id: UUID,
    default_settings: dict = {},
    **update_data,
) -> str:
    # Agent update query
    agent_id = str(agent_id)
    developer_id = str(developer_id)

    agent_update_cols, agent_update_vals = cozo_process_mutate_data(
        {
            **update_data,
            "agent_id": agent_id,
            "developer_id": developer_id,
            "updated_at": utcnow().timestamp(),
        }
    )

    agent_update_query = f"""
        # update the agent
        ?[{agent_update_cols}] <- {json.dumps(agent_update_vals)}

        :update agents {{
            {agent_update_cols}
        }}
        :returning
    """

    # Settings update query
    settings_cols, settings_vals = cozo_process_mutate_data(
        {
            **default_settings,
            "agent_id": agent_id,
        }
    )

    settings_update_query = f"""
        # update the agent settings
        ?[{settings_cols}] <- {json.dumps(settings_vals)}

        :update agent_default_settings {{
            {settings_cols}
        }}
    """

    # Combine the queries
    queries = [agent_update_query]

    if len(default_settings) == 0:
        queries.append(settings_update_query)

    combined_query = "}\n\n{".join(queries)
    combined_query = f"{{ {combined_query} }}"

    return combined_query

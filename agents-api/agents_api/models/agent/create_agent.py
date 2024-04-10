from uuid import UUID

import pandas as pd

from ...clients.cozo import client
from ...common.utils import json
from ...common.utils.cozo import cozo_process_mutate_data


def create_agent_query(
    agent_id: UUID,
    developer_id: UUID,
    name: str,
    about: str,
    instructions: list[str] = [],
    model: str = "julep-ai/samantha-1-turbo",
    metadata: dict = {},
    default_settings: dict = {},
) -> pd.DataFrame:
    assert model in ["julep-ai/samantha-1", "julep-ai/samantha-1-turbo"]

    settings_cols, settings_vals = cozo_process_mutate_data(
        {
            **default_settings,
            "agent_id": agent_id,
        }
    )

    # Create default agent settings
    default_settings_query = f"""
        ?[{settings_cols}] <- {json.dumps(settings_vals)}

        :insert agent_default_settings {{
            {settings_cols}
        }}
    """

    query_cols = json.dumps(
        [agent_id, developer_id, model, name, about, metadata, instructions]
    )
    # create the agent
    agent_query = f"""
        ?[agent_id, developer_id, model, name, about, metadata, instructions] <- [
            {query_cols}
        ]

        :insert agents {{
            developer_id,
            agent_id =>
            model,
            name,
            about,
            metadata,
            instructions,
        }}
        :returning
    """

    queries = [
        default_settings_query,
        agent_query,
    ]

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return client.run(query)

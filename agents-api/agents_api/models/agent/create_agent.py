from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client
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
    client: CozoClient = client,
) -> pd.DataFrame:
    assert model in ["julep-ai/samantha-1", "julep-ai/samantha-1-turbo"]

    settings_cols, settings_vals = cozo_process_mutate_data(
        {
            **default_settings,
            "agent_id": str(agent_id),
        }
    )

    # Create default agent settings
    default_settings_query = f"""
        ?[{settings_cols}] <- $settings_vals

        :insert agent_default_settings {{
            {settings_cols}
        }}
    """
    # create the agent
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

    return client.run(
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

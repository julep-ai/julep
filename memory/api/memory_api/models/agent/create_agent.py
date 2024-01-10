import json
from uuid import UUID

from ...common.utils.cozo import cozo_process_mutate_data


def create_agent_query(
    agent_id: UUID,
    developer_id: UUID,
    name: str,
    about: str,
    model: str = "julep-ai/samantha-1-turbo",
    default_settings: dict = {},
):
    assert model in ["julep-ai/samantha-1", "julep-ai/samantha-1-turbo"]
    agent_id = str(agent_id)

    settings_cols, settings_vals = cozo_process_mutate_data(
        {
            **default_settings,
            "agent_id": agent_id,
        }
    )

    return f"""
    {{
        # Create default agent settings
        ?[{settings_cols}] <- {json.dumps(settings_vals)}

        :insert agent_default_settings {{
            {settings_cols}
        }}
    }} {{
        # create the agent
        ?[agent_id, developer_id, model, name, about] <- [
            ["{agent_id}", "{developer_id}", "{model}", "{name}", "{about}"]
        ]

        :insert agents {{
            developer_id,
            agent_id =>
            model,
            name,
            about,
        }}
        :returning
    }}"""

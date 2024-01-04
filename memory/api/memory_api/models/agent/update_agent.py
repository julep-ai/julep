import json
from uuid import UUID

from ...common.utils.cozo import cozo_process_mutate_data


def update_agent_query(
    agent_id: UUID, name: str, about: str, model: str = "julep-ai/samantha-1-turbo", default_settings: dict = {}
):
    assert model in ["julep-ai/samantha-1", "julep-ai/samantha-1-turbo"]
    agent_id = str(agent_id)

    update_query = f"""
        # update the agent
        ?[agent_id, name, about, model, updated_at] <- [
            [to_uuid("{agent_id}"), "{name}", "{about}", "{model}", now()]
        ]

        :update agents {{
            agent_id =>
            name,
            about,
            model,
            updated_at,
        }}
        :returning
    """

    if len(default_settings) == 0:
        return update_query

    # Else add the settings
    settings_cols, settings_vals = cozo_process_mutate_data({
        **default_settings,
        "agent_id": agent_id,
    })

    update_query = f"""{{
        # update the agent settings
        ?[{settings_cols}] <- {json.dumps(settings_vals)}

        :update agent_default_settings {{
            {settings_cols}
        }}
    }} {{
        {update_query}
    }}
    """

    return update_query

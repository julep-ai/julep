from ...common.utils import json
from uuid import UUID

from ...autogen.openapi_model import Instruction
from ...common.utils.cozo import cozo_process_mutate_data

from ..instructions.create_instructions import create_instructions_query


def create_agent_query(
    agent_id: UUID,
    developer_id: UUID,
    name: str,
    about: str,
    instructions: list[Instruction] = [],
    model: str = "julep-ai/samantha-1-turbo",
    metadata: dict = {},
    default_settings: dict = {},
):
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

    query_cols = json.dumps([agent_id, developer_id, model, name, about, metadata])
    # create the agent
    agent_query = f"""
        ?[agent_id, developer_id, model, name, about, metadata] <- [
            {query_cols}
        ]

        :insert agents {{
            developer_id,
            agent_id =>
            model,
            name,
            about,
            metadata,
        }}
        :returning
    """

    queries = [
        default_settings_query,
        agent_query,
    ]

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    if instructions:
        query = create_instructions_query(agent_id, instructions) + "\n\n" + query

    return query

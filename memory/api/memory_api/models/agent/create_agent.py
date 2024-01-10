import json
from uuid import UUID

from ...autogen.openapi_model import Instruction
from ...common.utils.cozo import cozo_process_mutate_data


def create_agent_query(
    agent_id: UUID,
    developer_id: UUID,
    name: str,
    about: str,
    instructions: list[Instruction] = [],
    model: str = "julep-ai/samantha-1-turbo",
    default_settings: dict = {},
):
    assert model in ["julep-ai/samantha-1", "julep-ai/samantha-1-turbo"]
    agent_id = str(agent_id)
    instructions = [i.dict() for i in instructions]

    settings_cols, settings_vals = cozo_process_mutate_data(
        {
            **default_settings,
            "agent_id": agent_id,
        }
    )

    instruction_cols, instruction_rows = [], []

    for instruction_idx, instruction in enumerate(instructions):
        instruction_cols, new_instruction_rows = cozo_process_mutate_data(
            {
                **instruction,
                "instruction_idx": instruction_idx,
                "agent_id": agent_id,
            }
        )

        instruction_rows += new_instruction_rows

    # Create default agent settings
    default_settings_query = f"""
        ?[{settings_cols}] <- {json.dumps(settings_vals)}

        :insert agent_default_settings {{
            {settings_cols}
        }}
    """

    # Create instructions
    instruction_query = f"""
        ?[{instruction_cols}] <-  {json.dumps(instruction_rows)}

        :insert agent_instructions {{
            {instruction_cols}
        }}
    """

    # create the agent
    agent_query = f"""
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
    """

    queries = [
        default_settings_query,
        agent_query,
    ]

    if instructions:
        queries.insert(0, instruction_query)

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"
    return query

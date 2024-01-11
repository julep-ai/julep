import json
from uuid import UUID

from ...autogen.openapi_model import Instruction
from ...common.utils.cozo import cozo_process_mutate_data


def create_instructions_query(
    agent_id: UUID,
    instructions: list[Instruction] = [],
):
    agent_id = str(agent_id)
    instructions = [i.dict() for i in instructions]

    instruction_cols, instruction_rows = "", []

    for instruction_idx, instruction in enumerate(instructions):
        instruction_cols, new_instruction_rows = cozo_process_mutate_data(
            {
                **instruction,
                "instruction_idx": instruction_idx,
                "agent_id": agent_id,
            }
        )

        instruction_rows += new_instruction_rows

    # Create instructions
    instruction_query = f"""
    {{
        ?[{instruction_cols}] <-  {json.dumps(instruction_rows)}

        :insert agent_instructions {{
            {instruction_cols}
        }}
        :returning
    }}"""

    return instruction_query

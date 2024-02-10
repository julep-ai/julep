from uuid import UUID


def list_instructions_query(
    agent_id: UUID,
):
    agent_id = str(agent_id)

    return f"""
    {{
        input[agent_id] <- [[to_uuid("{agent_id}")]]

        ?[
            agent_id,
            instruction_idx,
            content,
            important,
            created_at,
        ] := input[agent_id],
            *agent_instructions {{
                agent_id,
                instruction_idx,
                content,
                important,
                created_at,
            }}
    }}"""

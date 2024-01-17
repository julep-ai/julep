from uuid import UUID


def delete_instructions_by_agent_query(agent_id: UUID) -> str:
    agent_id = str(agent_id)

    return f"""
    {{
        # Delete instructions
        input[agent_id] <- [[to_uuid("{agent_id}")]]
        ?[agent_id, instruction_idx] :=
            input[agent_id],
            *agent_instructions {{
                agent_id,
                instruction_idx,
            }}

        :delete agent_instructions {{
            agent_id,
            instruction_idx,
        }}
        :returning
    }}"""

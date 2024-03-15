from uuid import UUID


def embed_instructions_query(
    agent_id: UUID,
    instruction_indices: list[int],
    embeddings: list[list[float]],
):
    agent_id = str(agent_id)
    assert len(instruction_indices) == len(embeddings)

    records = "\n".join(
        [
            f'[to_uuid("{agent_id}"), {instruction_idx}, vec({embedding})],'
            for instruction_idx, embedding in zip(instruction_indices, embeddings)
        ]
    )

    return f"""
    {{
        ?[agent_id, instruction_idx, embedding] <- [
            {records}
        ]

        :update agent_instructions {{
            agent_id, 
            instruction_idx, 
            embedding,
        }}
        :returning
    }}"""

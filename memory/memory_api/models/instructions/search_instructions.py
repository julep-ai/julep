import json
from uuid import UUID


def search_instructions_query(
    agent_id: UUID,
    query_embedding: list[float],
    k: int = 3,
    confidence: float = 0.8,
):
    agent_id = str(agent_id)
    radius: float = 1.0 - confidence

    return f"""
    {{
        input[
            agent_id,
            query_embedding,
        ] <- [[
            to_uuid("{agent_id}"),
            vec({json.dumps(query_embedding)}),
        ]]

        # Keep instructions that are important
        ?[
            agent_id,
            instruction_idx,
            content,
            important,
            distance,
        ] := input[agent_id, query_embedding],
            *agent_instructions {{
                agent_id,
                instruction_idx,
                content,
                important,
            }},
            important = true,
            distance = 0.0

        ?[
            agent_id,
            instruction_idx,
            content,
            important,
            distance,
        ] := input[agent_id, query_embedding],
            ~agent_instructions:embedding_space {{
                agent_id,
                instruction_idx,
                content,
                important |
                query: query_embedding,
                k: {k},
                ef: 128,
                radius: {radius},
                bind_distance: distance,
                filter: important == false,
            }}

        :sort instruction_idx
    }}"""

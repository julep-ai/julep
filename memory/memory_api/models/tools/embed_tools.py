import json
from uuid import UUID


def embed_functions_query(
    agent_id: UUID,
    tool_ids: list[UUID],
    embeddings: list[list[float]],
):
    agent_id = str(agent_id)
    tool_ids = [str(id) for id in tool_ids]
    assert len(tool_ids) == len(embeddings)

    records = "\n".join(
        [
            f'[to_uuid("{agent_id}"), to_uuid("{tool_id}"), vec({json.dumps(embedding)})],'
            for tool_id, embedding in zip(tool_ids, embeddings)
        ]
    )

    return f"""
    {{
        ?[agent_id, tool_id, embedding] <- [
            {records}
        ]

        :update agent_functions {{
            agent_id, tool_id, embedding
        }}
        :returning
    }}"""

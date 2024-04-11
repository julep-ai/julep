from uuid import UUID

import pandas as pd

from ...clients.cozo import client


def embed_functions_query(
    agent_id: UUID,
    tool_ids: list[UUID],
    embeddings: list[list[float]],
) -> pd.DataFrame:
    agent_id = str(agent_id)
    tool_ids = [str(id) for id in tool_ids]
    assert len(tool_ids) == len(embeddings)

    records = "\n".join(
        [
            f'[to_uuid("{agent_id}"), to_uuid("{tool_id}"), vec({embedding})],'
            for tool_id, embedding in zip(tool_ids, embeddings)
        ]
    )

    query = f"""
    {{
        ?[agent_id, tool_id, embedding] <- [
            {records}
        ]

        :update agent_functions {{
            agent_id, tool_id, embedding
        }}
        :returning
    }}"""

    return client.run(query)

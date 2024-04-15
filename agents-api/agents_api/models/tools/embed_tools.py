from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


def embed_functions_query(
    agent_id: UUID,
    tool_ids: list[UUID],
    embeddings: list[list[float]],
    client: CozoClient = client,
) -> pd.DataFrame:
    agent_id = str(agent_id)
    tool_ids = [str(id) for id in tool_ids]
    assert len(tool_ids) == len(embeddings)

    records = [
        [agent_id, tool_id, embedding]
        for tool_id, embedding in zip(tool_ids, embeddings)
    ]

    query = """
    {
        ?[agent_id, tool_id, embedding] <- $records

        :update agent_functions {
            agent_id, tool_id, embedding
        }
        :returning
    }"""

    return client.run(query, {"records": records})

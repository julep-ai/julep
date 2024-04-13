from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


def get_function_by_id_query(
    agent_id: UUID,
    tool_id: UUID,
    client: CozoClient = client,
) -> pd.DataFrame:
    agent_id = str(agent_id)
    tool_id = str(tool_id)

    query = """
    {
        input[agent_id, tool_id] <- [[to_uuid($agent_id), to_uuid($tool_id)]]

        ?[
            agent_id,
            tool_id,
            name,
            description,
            parameters,
            updated_at,
            created_at,
        ] := input[agent_id, tool_id],
            *agent_functions {
                agent_id,
                tool_id,
                name,
                description,
                parameters,
                updated_at,
                created_at,
            }
    }"""

    return client.run(query, {"agent_id": agent_id, "tool_id": tool_id})

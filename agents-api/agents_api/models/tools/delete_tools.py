from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


def delete_function_by_id_query(
    agent_id: UUID,
    tool_id: UUID,
    client: CozoClient = client,
) -> pd.DataFrame:
    agent_id = str(agent_id)
    tool_id = str(tool_id)

    query = """
    {
        # Delete function
        ?[tool_id, agent_id] <- [[
            to_uuid($tool_id),
            to_uuid($agent_id),
        ]]

        :delete agent_functions {
            tool_id,
            agent_id,
        }
        :returning
    }"""

    return client.run(query, {"tool_id": tool_id, "agent_id": agent_id})

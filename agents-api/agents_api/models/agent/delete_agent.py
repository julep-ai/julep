from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


def delete_agent_query(
    developer_id: UUID, agent_id: UUID, client: CozoClient = client
) -> pd.DataFrame:
    query = """
    {
        # Delete default agent settings
        ?[agent_id] <- [[$agent_id]]

        :delete agent_default_settings {
            agent_id
        }
    } {
        # Delete the agent
        ?[agent_id, developer_id] <- [[$agent_id, $developer_id]]

        :delete agents {
            developer_id,
            agent_id
        }
    }"""

    return client.run(query, {"agent_id": str(agent_id), "developer_id": str(developer_id)})

from uuid import UUID

import pandas as pd

from ...clients.cozo import client


def delete_agent_query(developer_id: UUID, agent_id: UUID) -> pd.DataFrame:
    query = f"""
    {{
        # Delete default agent settings
        ?[agent_id] <- [["{agent_id}"]]

        :delete agent_default_settings {{
            agent_id
        }}
    }} {{
        # Delete the agent
        ?[agent_id, developer_id] <- [["{agent_id}", "{developer_id}"]]

        :delete agents {{
            developer_id,
            agent_id
        }}
    }}"""

    return client.run(query)

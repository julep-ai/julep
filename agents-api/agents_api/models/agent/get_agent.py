from uuid import UUID

import pandas as pd

from ...clients.cozo import client


def get_agent_query(developer_id: UUID, agent_id: UUID) -> pd.DataFrame:
    query = f"""
    {{
        input[agent_id, developer_id] <- [[to_uuid("{agent_id}"), to_uuid("{developer_id}")]]

        ?[
            id,
            model,
            name,
            about,
            created_at,
            updated_at,
            metadata,
            default_settings,
        ] := input[id, developer_id],
            *agents {{
                developer_id,
                agent_id: id,
                model,
                name,
                about,
                created_at,
                updated_at,
                metadata,
            }},
            *agent_default_settings {{
                agent_id: id,
                frequency_penalty,
                presence_penalty,
                length_penalty,
                repetition_penalty,
                top_p,
                temperature,
                min_p,
                preset,
            }},
            default_settings = {{
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty,
                "length_penalty": length_penalty,
                "repetition_penalty": repetition_penalty,
                "top_p": top_p,
                "temperature": temperature,
                "min_p": min_p,
                "preset": preset,
            }}
    }}
    """

    return client.run(query)

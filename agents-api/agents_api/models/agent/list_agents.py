from typing import Any
from uuid import UUID

import pandas as pd

from ...clients.cozo import client
from ...common.utils import json


def list_agents_query(
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    metadata_filter: dict[str, Any] = {},
) -> pd.DataFrame:
    metadata_filter_str = ", ".join(
        [
            f"metadata->{json.dumps(k)} == {json.dumps(v)}"
            for k, v in metadata_filter.items()
        ]
    )

    query = f"""
    {{
        input[developer_id] <- [[to_uuid("{developer_id}")]]

        ?[
            id,
            model,
            name,
            about,
            created_at,
            updated_at,
            metadata,
        ] := input[developer_id],
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
            {metadata_filter_str}
        
        :limit {limit}
        :offset {offset}
        :sort -created_at
    }}"""

    return client.run(query)

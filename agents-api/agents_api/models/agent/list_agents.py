import json
from typing import Any
from uuid import UUID


def list_agents_query(
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    metadata_filter: dict[str, Any] = {},
):
    metadata_filter_str = ", ".join(
        [f'metadata->"{json.dumps(k)}" == {v}' for k, v in metadata_filter.items()]
    )

    return f"""
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

from typing import Any
from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client

from ...common.utils import json


def list_users_query(
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    metadata_filter: dict[str, Any] = {},
    client: CozoClient = client,
) -> pd.DataFrame:
    metadata_filter_str = ", ".join(
        [
            f"metadata->{json.dumps(k)} == {json.dumps(v)}"
            for k, v in metadata_filter.items()
        ]
    )

    query = f"""
    input[developer_id] <- [[to_uuid($developer_id)]]

    ?[
        id,
        name,
        about,
        created_at,
        updated_at,
        metadata,
    ] :=
        input[developer_id],
        *users {{
            user_id: id,
            developer_id,
            name,
            about,
            created_at,
            updated_at,
            metadata,
        }},
        {metadata_filter_str}

    :limit $limit
    :offset $offset
    :sort -created_at
    """

    return client.run(
        query, {"developer_id": str(developer_id), "limit": limit, "offset": offset}
    )

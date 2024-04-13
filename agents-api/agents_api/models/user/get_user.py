from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


def get_user_query(
    developer_id: UUID,
    user_id: UUID,
    client: CozoClient = client,
) -> pd.DataFrame:
    # Convert UUIDs to strings for query compatibility.
    user_id = str(user_id)
    developer_id = str(developer_id)

    query = """
    input[developer_id, user_id] <- [[to_uuid($developer_id), to_uuid($user_id)]]

    ?[
        id,
        name,
        about,
        created_at,
        updated_at,
        metadata,
    ] := input[developer_id, id],
        *users {
            user_id: id,
            developer_id,
            name,
            about,
            created_at,
            updated_at,
            metadata,
        }"""

    return client.run(query, {"developer_id": developer_id, "user_id": user_id})

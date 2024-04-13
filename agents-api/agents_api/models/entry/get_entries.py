from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


def get_entries_query(
    session_id: UUID, limit: int = 100, offset: int = 0, client: CozoClient = client
) -> pd.DataFrame:
    query = """
    {
        ?[
            session_id,
            entry_id,
            role,
            name,
            content,
            source,
            token_count,
            created_at,
            timestamp,
        ] := *entries{
            session_id,
            entry_id,
            role,
            name,
            content,
            source,
            token_count,
            created_at,
            timestamp,
        },
        source in ["api_request", "api_response"],
        session_id = to_uuid($session_id),

        :sort timestamp
        :limit $limit
        :offset $offset
    }"""

    results = client.run(
        query, {"session_id": str(session_id), "limit": limit, "offset": offset}
    )

    return results

from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


def get_entries_query(
    session_id: UUID, limit: int = 100, offset: int = 0, client: CozoClient = client
) -> pd.DataFrame:
    query = """
    {
        input[session_id] <- [[
            to_uuid($session_id),
        ]]

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
        ] := input[session_id],
            *entries{
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
            source == "api_request" || source == "api_response",

        :sort timestamp
        :limit $limit
        :offset $offset
    }"""

    return client.run(
        query, {"session_id": str(session_id), "limit": limit, "offset": offset}
    )

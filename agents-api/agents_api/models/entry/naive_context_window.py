from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


def naive_context_window_query(
    session_id: UUID, client: CozoClient = client
) -> pd.DataFrame:
    session_id = str(session_id)

    query = f"""
    {{
        # In this query, we are going to collect all session entries for a `session_id`.
        # - filter(source=="api_request" or source=="api_response")

        input[session_id] <- [[
            to_uuid("{session_id}"),
        ]]

        ?[role, name, content, token_count, created_at, timestamp] :=
            input[session_id],
            *entries{{
                session_id,
                source,
                role,
                name,
                content,
                token_count,
                created_at,
                timestamp,
            }},
            source == "api_request" || source == "api_response",

        :sort timestamp
    }}
    """

    return client.run(query)

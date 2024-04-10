from uuid import UUID

import pandas as pd

from ...clients.cozo import client


def delete_entries_query(session_id: UUID) -> pd.DataFrame:
    query = f"""
    {{
        input[session_id] <- [[
            to_uuid("{session_id}"),
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
            *entries{{
                session_id,
                entry_id,
                role,
                name,
                content,
                source,
                token_count,
                created_at,
                timestamp,
            }}
        
        :delete entries {{
            session_id,
            entry_id,
            role,
            name,
            content,
            source,
            token_count,
            created_at,
            timestamp,
        }}
    }}"""

    return client.run(query)

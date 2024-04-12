from typing import Literal
from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


def ensure_owner_exists_query(
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
    client: CozoClient = client,
) -> pd.DataFrame:
    owner_id = str(owner_id)

    query = f"""{{
        input[{owner_type}_id] <- [[to_uuid($owner_id)]]

        ?[
            {owner_type}_id,
        ] := input[{owner_type}_id],
            *{owner_type}s {{
                {owner_type}_id,
            }}
    }}"""

    return client.run(query, {"owner_id": owner_id})


def list_docs_snippets_by_owner_query(
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
    client: CozoClient = client,
):
    owner_id = str(owner_id)

    query = f"""
    {{
        input[{owner_type}_id] <- [[to_uuid($owner_id)]]

        ?[
            {owner_type}_id,
            doc_id,
            title,
            snippet,
            snippet_idx,
            created_at,
            metadata,
        ] := input[{owner_type}_id],
            *{owner_type}_docs {{
                {owner_type}_id,
                doc_id,
                created_at,
                metadata,
            }},
            *information_snippets {{
                doc_id,
                snippet_idx,
                title,
                snippet,
            }}
    }}"""

    return client.run(query, {"owner_id": owner_id})

from typing import Literal
from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


def get_docs_snippets_by_id_query(
    owner_type: Literal["user", "agent"],
    doc_id: UUID,
    client: CozoClient = client,
) -> pd.DataFrame:
    doc_id = str(doc_id)

    query = f"""
    {{
        input[doc_id] <- [[to_uuid("{doc_id}")]]

        ?[
            {owner_type}_id,
            doc_id,
            title,
            snippet,
            snippet_idx,
            created_at,
            embed_instruction,
            metadata,
        ] := input[doc_id],
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
                embed_instruction,
            }}
    }}"""

    return client.run(query)

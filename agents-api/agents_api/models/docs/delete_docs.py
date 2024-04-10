from typing import Literal
from uuid import UUID

import pandas as pd

from ...clients.cozo import client


def delete_docs_by_id_query(
    owner_type: Literal["user", "agent"], owner_id: UUID, doc_id: UUID
) -> pd.DataFrame:
    owner_id = str(owner_id)
    doc_id = str(doc_id)

    query = f"""
    {{
        # Delete snippets
        input[doc_id] <- [[to_uuid("{doc_id}")]]
        ?[doc_id, snippet_idx] :=
            input[doc_id],
            *information_snippets {{
                doc_id,
                snippet_idx,
            }}

        :delete information_snippets {{
            doc_id,
            snippet_idx
        }}
    }} {{
        # Delete the docs
        ?[doc_id, {owner_type}_id] <- [[
            to_uuid("{doc_id}"),
            to_uuid("{owner_id}"),
        ]]

        :delete {owner_type}_docs {{
            doc_id,
            {owner_type}_id,
        }}
        :returning
    }}"""

    return client.run(query)

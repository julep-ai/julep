"""This module contains functions for querying document-related data from the 'cozodb' database using datalog queries."""

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

    # Query to check if an owner (user or agent) exists in the database
    query = f"""{{
        # Convert owner_id to UUID and set as input
        input[{owner_type}_id] <- [[to_uuid($owner_id)]]

        # Retrieve owner_id if it exists in the database
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

    # Query to retrieve document snippets by owner (user or agent)
    query = f"""
    {{
        # Convert owner_id to UUID and set as input
        input[{owner_type}_id] <- [[to_uuid($owner_id)]]

        # Retrieve documents and snippets associated with the owner
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

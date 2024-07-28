"""This module contains functions for querying document-related data from the 'cozodb' database using datalog queries."""

import json
from typing import Any, Literal
from uuid import UUID

from beartype import beartype

from ..utils import cozo_query


@cozo_query
@beartype
def ensure_owner_exists_query(
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
) -> tuple[str, dict]:
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

    return (query, {"owner_id": owner_id})


@cozo_query
@beartype
def list_docs_snippets_by_owner_query(
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
    metadata_filter: dict[str, Any] = {},
) -> tuple[str, dict]:
    owner_id = str(owner_id)

    metadata_filter_str = ", ".join(
        [
            f"metadata->{json.dumps(k)} == {json.dumps(v)}"
            for k, v in metadata_filter.items()
        ]
    )

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
            }},
            {metadata_filter_str}
    }}"""

    return (query, {"owner_id": owner_id})

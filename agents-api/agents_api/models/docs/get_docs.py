"""Module for retrieving document snippets from the CozoDB based on document IDs."""

from typing import Literal
from uuid import UUID

from beartype import beartype

from ..utils import cozo_query


@cozo_query
@beartype
def get_docs_snippets_by_id_query(
    owner_type: Literal["user", "agent"],
    doc_id: UUID,
) -> tuple[str, dict]:
    """
    Retrieves snippets of documents by their ID from the CozoDB.

    Parameters:
        owner_type (Literal["user", "agent"]): The type of the owner of the document.
        doc_id (UUID): The unique identifier of the document.
        client (CozoClient, optional): The CozoDB client instance. Defaults to a pre-configured client.

    Returns:
        pd.DataFrame: A DataFrame containing the document snippets and related metadata.
    """

    doc_id = str(doc_id)

    query = f"""
    {{
        input[doc_id] <- [[to_uuid($doc_id)]]

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

    return (query, {"doc_id": doc_id})

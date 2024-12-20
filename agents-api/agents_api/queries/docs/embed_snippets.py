from typing import Literal
from uuid import UUID

from beartype import beartype
from sqlglot import parse_one

from ..utils import pg_query

# TODO: This is a placeholder for the actual query
vectorizer_query = None


@pg_query
@beartype
async def embed_snippets(
    *,
    developer_id: UUID,
    doc_id: UUID,
    owner_type: Literal["user", "agent"] | None = None,
    owner_id: UUID | None = None,
) -> tuple[str, list]:
    """
    Trigger the vectorizer to generate embeddings for documents.

    Parameters:
        developer_id (UUID): The ID of the developer.
        doc_id (UUID): The ID of the document.
        owner_type (Literal["user", "agent"]): The type of the owner of the documents.
        owner_id (UUID): The ID of the owner of the documents.

    Returns:
        tuple[str, list]: SQL query and parameters for embedding the snippets.
    """
    return (
        vectorizer_query,
        [developer_id, doc_id, owner_type, owner_id],
    )

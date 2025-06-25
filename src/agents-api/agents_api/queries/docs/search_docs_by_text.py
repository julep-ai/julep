from typing import Any, Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import DocReference
from ...common.nlp import text_to_keywords
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class
from .utils import transform_to_doc_reference

# SQL query for searching docs by text
search_docs_text_query = """
SELECT * FROM search_by_text(
    $1::uuid,    -- developer_id
    $2::text,    -- query_text
    $3::text[],  -- owner_types
    $4::uuid[],  -- owner_ids
    $5::text,    -- search_language
    $6::int,     -- k
    $7::jsonb,   -- metadata_filter
    $8::float    -- similarity_threshold (default value)
);
"""


@rewrap_exceptions(common_db_exceptions("doc", ["search"]))
@wrap_in_class(
    DocReference,
    transform=transform_to_doc_reference,
)
@pg_query
@beartype
async def search_docs_by_text(
    *,
    developer_id: UUID,
    owners: list[tuple[Literal["user", "agent"], UUID]],
    query: str,
    k: int = 3,
    metadata_filter: dict[str, Any] | None = None,
    search_language: str | None = "english_unaccent",
    trigram_similarity_threshold: float | None = None,  # Set to None to disable trigram search
    extract_keywords: bool = False,
) -> tuple[str, list]:
    """
    Full-text search on docs using the search_tsv column.

    Parameters:
        developer_id (UUID): The ID of the developer.
        query (str): The text to search for.
        owners (list[tuple[Literal["user", "agent"], UUID]]): List of (owner_type, owner_id) tuples.
        k (int): Maximum number of results to return.
        search_language (str): Language for text search (default: "english").
        metadata_filter (dict): Metadata filter criteria.
        trigram_similarity_threshold (float): Similarity threshold for trigram search.
        extract_keywords (bool): Whether to extract keywords from the query.
        connection_pool (asyncpg.Pool): Database connection pool.

    Returns:
        tuple[str, list]: SQL query and parameters for searching the documents.
    """

    # AIDEV-NOTE: avoid mutable default; initialize metadata_filter
    metadata_filter = metadata_filter if metadata_filter is not None else {}
    if k < 1:
        raise HTTPException(status_code=400, detail="k must be >= 1")

    # Extract owner types and IDs
    owner_types: list[str] = [owner[0] for owner in owners]
    owner_ids: list[UUID] = [owner[1] for owner in owners]

    # Pre-process rawtext query if extract_keywords is True
    if extract_keywords:
        keywords = text_to_keywords(query, split_chunks=True)
        query = " OR ".join(keywords)

    return (
        search_docs_text_query,
        [
            developer_id,
            query,
            owner_types,
            owner_ids,
            search_language,
            k,
            metadata_filter,
            trigram_similarity_threshold,
        ],
    )

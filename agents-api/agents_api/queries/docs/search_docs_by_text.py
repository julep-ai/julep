from typing import Any, Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import DocReference
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class
from .utils import transform_to_doc_reference

# Raw query for text search
search_docs_text_query = """
SELECT * FROM search_by_text(
    $1, -- developer_id
    $2, -- query
    $3, -- owner_types
    $4, -- owner_ids
    $5, -- search_language
    $6, -- k
    $7 -- metadata_filter
)
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
    metadata_filter: dict[str, Any] = {},
    search_language: str | None = "english",
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
        connection_pool (asyncpg.Pool): Database connection pool.

    Returns:
        tuple[str, list]: SQL query and parameters for searching the documents.
    """
    if k < 1:
        raise HTTPException(status_code=400, detail="k must be >= 1")

    # Extract owner types and IDs
    owner_types: list[str] = [owner[0] for owner in owners]
    owner_ids: list[str] = [str(owner[1]) for owner in owners]

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
        ],
    )

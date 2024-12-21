from typing import Any, Literal, List
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
import asyncpg
import json

from ...autogen.openapi_model import DocReference
from ..utils import pg_query, wrap_in_class, rewrap_exceptions, partialclass

search_docs_text_query = (
    """
    SELECT * FROM search_by_text(
        $1, -- developer_id
        $2, -- query
        $3, -- owner_types
        ( SELECT array_agg(*)::UUID[] FROM jsonb_array_elements($4) )
    )
    """
)


@rewrap_exceptions(
    {
        asyncpg.UniqueViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        )
    }
)
@wrap_in_class(
    DocReference,
    transform=lambda d: {
        "owner": {
            "id": d["owner_id"],
            "role": d["owner_type"],
        },
        "metadata": d.get("metadata", {}),
        **d,
    },
)
@pg_query(debug=True)
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
    owner_types = [owner[0] for owner in owners]
    owner_ids = [owner[1] for owner in owners]
    
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

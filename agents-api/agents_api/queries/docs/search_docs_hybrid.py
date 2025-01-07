from typing import Any, Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import DocReference
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import (
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)
from .utils import transform_to_doc_reference

# Raw query for hybrid search
search_docs_hybrid_query = """
SELECT * FROM search_hybrid(
    $1, -- developer_id
    $2, -- text_query
    $3::vector(1024), -- embedding
    $4::text[], -- owner_types
    $5::uuid[], -- owner_ids
    $6, -- k
    $7, -- alpha
    $8, -- confidence
    $9, -- metadata_filter
    $10 -- search_language
)
"""


@rewrap_exceptions(common_db_exceptions("doc", ["search"]))
@wrap_in_class(
    DocReference,
    transform=transform_to_doc_reference,
)
@pg_query
@beartype
async def search_docs_hybrid(
    developer_id: UUID,
    owners: list[tuple[Literal["user", "agent"], UUID]],
    text_query: str = "",
    embedding: list[float] | None = None,
    k: int = 10,
    alpha: float = 0.5,
    metadata_filter: dict[str, Any] = {},
    search_language: str = "english",
    confidence: int | float = 0.5,
) -> tuple[str, list]:
    """
    Hybrid text-and-embedding doc search. We get top-K from each approach,
    then fuse them client-side. Adjust concurrency or approach as you like.

    Parameters:
        developer_id (UUID): The unique identifier for the developer.
        text_query (str): The text query to search for.
        embedding (List[float]): The embedding to search for.
        k (int): The number of results to return.
        alpha (float): The weight for the embedding results.
        owner_type (Literal["user", "agent", "org"] | None): The type of the owner.
        owner_id (UUID | None): The ID of the owner.

    Returns:
        tuple[str, list]: The SQL query and parameters for the search.
    """

    if k < 1:
        raise HTTPException(status_code=400, detail="k must be >= 1")

    if not text_query and not embedding:
        raise HTTPException(status_code=400, detail="Empty query provided")

    if not embedding:
        raise HTTPException(status_code=400, detail="Empty embedding provided")

    # Convert query_embedding to a string
    embedding_str = f"[{', '.join(map(str, embedding))}]"

    # Extract owner types and IDs
    owner_types: list[str] = [owner[0] for owner in owners]
    owner_ids: list[str] = [str(owner[1]) for owner in owners]

    return (
        search_docs_hybrid_query,
        [
            developer_id,
            text_query,
            embedding_str,
            owner_types,
            owner_ids,
            k,
            alpha,
            1.0 - confidence,
            metadata_filter,
            search_language,
        ],
    )

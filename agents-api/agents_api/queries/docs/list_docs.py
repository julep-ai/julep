"""
This module contains the functionality for listing documents from the PostgreSQL database.
It constructs and executes SQL queries to fetch document details based on various filters.
"""

from typing import Any, Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException

from ...autogen.openapi_model import Doc
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class
from .utils import transform_doc

# Base query for listing docs with aggregated content and embeddings
base_docs_query = """
SELECT
    d.doc_id,
    d.developer_id,
    d.title,
    array_agg(d.content ORDER BY d.index) as content,
    array_agg(d.index ORDER BY d.index) as indices,
    array_agg(CASE WHEN $2 THEN NULL ELSE e.embedding END ORDER BY d.index) as embeddings,
    d.modality,
    d.embedding_model,
    d.embedding_dimensions,
    d.language,
    d.metadata,
    d.created_at
FROM docs d
JOIN doc_owners doc_own
    ON d.developer_id = doc_own.developer_id
    AND d.doc_id = doc_own.doc_id
LEFT JOIN docs_embeddings e
    ON d.doc_id = e.doc_id
    AND d.index = e.index
WHERE d.developer_id = $1
    AND doc_own.owner_type = $3
    AND doc_own.owner_id = $4
"""


@rewrap_exceptions(common_db_exceptions("doc", ["list"]))
@wrap_in_class(
    Doc,
    one=False,
    transform=transform_doc,
)
@pg_query
@beartype
async def list_docs(
    *,
    developer_id: UUID,
    owner_id: UUID,
    owner_type: Literal["user", "agent"],
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict[str, Any] = {},
    include_without_embeddings: bool = False,
) -> tuple[str, list]:
    """
    Lists docs with pagination and sorting, aggregating content chunks and embeddings.

    Parameters:
        developer_id (UUID): The ID of the developer.
        owner_id (UUID): The ID of the owner of the documents (required).
        owner_type (Literal["user", "agent"]): The type of the owner of the documents (required).
        limit (int): The number of documents to return.
        offset (int): The number of documents to skip.
        sort_by (Literal["created_at", "updated_at"]): The field to sort by.
        direction (Literal["asc", "desc"]): The direction to sort by.
        metadata_filter (dict[str, Any]): The metadata filter to apply.
        include_without_embeddings (bool): Whether to include documents without embeddings.

    Returns:
        tuple[str, list]: SQL query and parameters for listing the documents.

    Raises:
        HTTPException: If invalid parameters are provided.
    """
    # Validate parameters
    if direction.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort direction")

    if sort_by not in ["created_at", "updated_at"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be greater than 0")

    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be non-negative")

    # Start with the base query
    query = base_docs_query
    params = [developer_id, include_without_embeddings, owner_type, owner_id]

    # Add metadata filtering before GROUP BY
    if metadata_filter:
        for key, value in metadata_filter.items():
            query += f" AND d.metadata->>${len(params) + 1} = ${len(params) + 2}"
            params.extend([key, value])

    # Add GROUP BY clause
    query += """
    GROUP BY
        d.doc_id,
        d.developer_id,
        d.title,
        d.modality,
        d.embedding_model,
        d.embedding_dimensions,
        d.language,
        d.metadata,
        d.created_at"""

    # Add sorting and pagination
    query += (
        f" ORDER BY {sort_by} {direction} LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    )
    params.extend([limit, offset])

    return query, params

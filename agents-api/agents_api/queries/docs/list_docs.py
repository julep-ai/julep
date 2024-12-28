"""
This module contains the functionality for listing documents from the PostgreSQL database.
It constructs and executes SQL queries to fetch document details based on various filters.
"""

from typing import Any, Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
import ast

from ...autogen.openapi_model import Doc
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Base query for listing docs with aggregated content and embeddings
base_docs_query = parse_one("""
WITH doc_data AS (
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
    WHERE d.developer_id = $1
        AND doc_own.owner_type = $3 
        AND doc_own.owner_id = $4
    GROUP BY
        d.doc_id,
        d.developer_id,
        d.title,
        d.modality,
        d.embedding_model,
        d.embedding_dimensions,
        d.language,
        d.metadata,
        d.created_at
)
SELECT * FROM doc_data
""").sql(pretty=True)


def transform_list_docs(d: dict) -> dict:
    content = d["content"][0] if len(d["content"]) == 1 else d["content"]

    embeddings = d["embeddings"][0] if len(d["embeddings"]) == 1 else d["embeddings"]

    try:
        # Embeddings are retreived as a string, so we need to evaluate it
        embeddings = ast.literal_eval(embeddings)
    except Exception as e:
        raise ValueError(f"Error evaluating embeddings: {e}")

    if embeddings and all((e is None) for e in embeddings):
        embeddings = None

    transformed = {
        **d,
        "id": d["doc_id"],
        "content": content,
        "embeddings": embeddings,
    }
    return transformed


@rewrap_exceptions(
    {
        asyncpg.NoDataFoundError: partialclass(
            HTTPException,
            status_code=404,
            detail="No documents found",
        ),
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer or owner does not exist",
        ),
    }
)
@wrap_in_class(
    Doc,
    one=False,
    transform=transform_list_docs,
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
    if direction.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort direction")

    if sort_by not in ["created_at", "updated_at"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if limit > 100 or limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be >= 0")

    # Start with the base query
    query = base_docs_query
    params = [developer_id, include_without_embeddings, owner_type, owner_id]

    # Add metadata filtering
    if metadata_filter:
        for key, value in metadata_filter.items():
            query += f" AND metadata->>'{key}' = ${len(params) + 1}"
            params.append(value)

    # Add sorting and pagination
    query += f" ORDER BY {sort_by} {direction} LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    params.extend([limit, offset])

    return query, params

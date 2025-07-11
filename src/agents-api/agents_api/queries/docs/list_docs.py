"""
This module contains the functionality for listing documents from the PostgreSQL database.
It constructs and executes SQL queries to fetch document details based on various filters.
"""

from typing import Annotated, Any, Literal
from uuid import UUID

from beartype import beartype
from beartype.vale import Is

from ...autogen.openapi_model import Doc
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import (
    build_metadata_filter_conditions,
    make_num_validator,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)
from .utils import transform_doc

# Base query for listing docs with aggregated content and embeddings
base_docs_query = """
SELECT
    d.doc_id,
    d.developer_id,
    d.title,
    array_agg(d.content ORDER BY d.index) as content,
    array_agg(d.index ORDER BY d.index) as indices,
    array_agg(CASE WHEN $2 THEN e.embedding ELSE NULL END ORDER BY d.index) as embeddings,
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
    limit: Annotated[
        int,
        Is[
            make_num_validator(
                min_value=1, max_value=100, err_msg="Limit must be between 1 and 100"
            )
        ],
    ] = 100,
    offset: Annotated[
        int, Is[make_num_validator(min_value=0, err_msg="Offset must be >= 0")]
    ] = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict[str, Any] | None = None,
    include_embeddings: bool = True,
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
        include_embeddings (bool): Whether to include embeddings in the response.
            Defaults to True for backward compatibility.

    Returns:
        tuple[str, list]: SQL query and parameters for listing the documents.

    Raises:
        HTTPException: If invalid parameters are provided.
    """
    # if direction.lower() not in ["asc", "desc"]:
    #     raise HTTPException(status_code=400, detail="Invalid sort direction")

    # if sort_by not in ["created_at", "updated_at"]:
    #     raise HTTPException(status_code=400, detail="Invalid sort field")

    # AIDEV-NOTE: avoid mutable default; initialize metadata_filter
    metadata_filter = metadata_filter if metadata_filter is not None else {}
    # Start with the base query
    query = base_docs_query
    # AIDEV-NOTE: Bandwidth optimization - pass include_embeddings to control embedding retrieval
    params = [developer_id, include_embeddings, owner_type, owner_id]

    # Add metadata filtering before GROUP BY using the utility function with table alias
    metadata_conditions, params = build_metadata_filter_conditions(
        params, metadata_filter, table_alias="d."
    )
    query += metadata_conditions

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

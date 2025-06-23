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
from ..sql_utils import SafeQueryBuilder
from ..utils import (
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
    # if direction.lower() not in ["asc", "desc"]:
    #     raise HTTPException(status_code=400, detail="Invalid sort direction")

    # if sort_by not in ["created_at", "updated_at"]:
    #     raise HTTPException(status_code=400, detail="Invalid sort field")

    # AIDEV-NOTE: avoid mutable default; initialize metadata_filter
    metadata_filter = metadata_filter if metadata_filter is not None else {}

    # Build query using SafeQueryBuilder to prevent SQL injection
    builder = SafeQueryBuilder(
        base_docs_query, [developer_id, include_without_embeddings, owner_type, owner_id]
    )

    # Add metadata filtering using SafeQueryBuilder's condition system
    if metadata_filter:
        for key, value in metadata_filter.items():
            builder.add_condition(" AND d.metadata->>{}::text = {}", key, str(value))

    # Add GROUP BY clause
    builder.add_raw_condition("""
    GROUP BY
        d.doc_id,
        d.developer_id,
        d.title,
        d.modality,
        d.embedding_model,
        d.embedding_dimensions,
        d.language,
        d.metadata,
        d.created_at""")

    # Add sorting and pagination with validation
    builder.add_order_by(
        sort_by, direction, allowed_fields={"created_at", "updated_at"}, table_prefix=""
    )
    builder.add_limit_offset(limit, offset)

    return builder.build()

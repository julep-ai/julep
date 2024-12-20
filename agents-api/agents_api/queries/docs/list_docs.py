import ast
from typing import Any, Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import Doc
from ..utils import pg_query, wrap_in_class

# Base query for listing docs
base_docs_query = parse_one("""
SELECT d.*
FROM docs d
LEFT JOIN doc_owners doc_own ON d.developer_id = doc_own.developer_id AND d.doc_id = doc_own.doc_id
WHERE d.developer_id = $1
""").sql(pretty=True)


@wrap_in_class(
    Doc,
    one=False,
    transform=lambda d: {
        **d,
        "id": d["doc_id"],
        "content": ast.literal_eval(d["content"])[0]
        if len(ast.literal_eval(d["content"])) == 1
        else ast.literal_eval(d["content"]),
        # "embeddings": d["embeddings"],
    },
)
@pg_query
@beartype
async def list_docs(
    *,
    developer_id: UUID,
    owner_id: UUID | None = None,
    owner_type: Literal["user", "agent"] | None = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict[str, Any] = {},
    include_without_embeddings: bool = False,
) -> tuple[str, list]:
    """
    Lists docs with optional owner filtering, pagination, and sorting.
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
    params = [developer_id]

    # Add owner filtering
    if owner_type and owner_id:
        query += " AND doc_own.owner_type = $2 AND doc_own.owner_id = $3"
        params.extend([owner_type, owner_id])

    # Add metadata filtering
    if metadata_filter:
        for key, value in metadata_filter.items():
            query += f" AND d.metadata->>'{key}' = ${len(params) + 1}"
            params.append(value)

    # Include or exclude documents without embeddings
    # if not include_without_embeddings:
    #     query += " AND d.embeddings IS NOT NULL"

    # Add sorting and pagination
    query += f" ORDER BY {sort_by} {direction} LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    params.extend([limit, offset])

    return query, params

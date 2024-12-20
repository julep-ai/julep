"""
Timescale-based listing of docs with optional owner filter and pagination.
"""
from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import Doc
from ..utils import pg_query, wrap_in_class

# Basic listing for all docs by developer
developer_docs_query = parse_one("""
SELECT d.*
FROM docs d
LEFT JOIN doc_owners do ON d.developer_id = do.developer_id AND d.doc_id = do.doc_id
WHERE d.developer_id = $1
ORDER BY
CASE
  WHEN $4 = 'created_at' AND $5 = 'asc' THEN d.created_at
  WHEN $4 = 'created_at' AND $5 = 'desc' THEN d.created_at
  WHEN $4 = 'updated_at' AND $5 = 'asc' THEN d.updated_at
  WHEN $4 = 'updated_at' AND $5 = 'desc' THEN d.updated_at
END DESC NULLS LAST
LIMIT $2
OFFSET $3;
""").sql(pretty=True)

# Listing for docs associated with a specific owner
owner_docs_query = parse_one("""
SELECT d.*
FROM docs d
JOIN doc_owners do ON d.developer_id = do.developer_id AND d.doc_id = do.doc_id
WHERE do.developer_id = $1
  AND do.owner_id = $6
  AND do.owner_type = $7
ORDER BY
CASE
  WHEN $4 = 'created_at' AND $5 = 'asc' THEN d.created_at
  WHEN $4 = 'created_at' AND $5 = 'desc' THEN d.created_at
  WHEN $4 = 'updated_at' AND $5 = 'asc' THEN d.updated_at
  WHEN $4 = 'updated_at' AND $5 = 'desc' THEN d.updated_at
END DESC NULLS LAST
LIMIT $2
OFFSET $3;
""").sql(pretty=True)


@wrap_in_class(
    Doc,
    one=False,
    transform=lambda d: {
        **d,
        "id": d["doc_id"],
    },
)
@pg_query
@beartype
async def list_docs(
    *,
    developer_id: UUID,
    owner_id: UUID | None = None,
    owner_type: Literal["user", "agent", "org"] | None = None,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
) -> tuple[str, list]:
    """
    Lists docs with optional owner filtering, pagination, and sorting.
    """
    if direction.lower() not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort direction")

    if limit > 100 or limit < 1:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset must be >= 0")

    params = [developer_id, limit, offset, sort_by, direction]
    if owner_id and owner_type:
        params.extend([owner_id, owner_type])
        query = owner_docs_query
    else:
        query = developer_docs_query

    return (query, params)

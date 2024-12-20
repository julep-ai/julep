"""
Timescale-based creation of docs.

Mirrors the structure of create_file.py, but uses the docs/doc_owners tables.
"""

import base64
import hashlib
from typing import Any, Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateDocRequest, Doc
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Base INSERT for docs
doc_query = parse_one("""
INSERT INTO docs (
    developer_id,
    doc_id,
    title,
    content,
    index,
    modality,
    embedding_model,
    embedding_dimensions,
    language,
    metadata
)
VALUES (
    $1, -- developer_id
    $2, -- doc_id
    $3, -- title
    $4, -- content
    $5, -- index
    $6, -- modality
    $7, -- embedding_model
    $8, -- embedding_dimensions
    $9, -- language
    $10 -- metadata (JSONB)
)
RETURNING *;
""").sql(pretty=True)

# Owner association query for doc_owners
doc_owner_query = parse_one("""
WITH inserted_owner AS (
    INSERT INTO doc_owners (
        developer_id,
        doc_id,
        owner_type,
        owner_id
    )
    VALUES ($1, $2, $3, $4)
    RETURNING doc_id
)
SELECT d.*
FROM inserted_owner io
JOIN docs d ON d.doc_id = io.doc_id;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.UniqueViolationError: partialclass(
            HTTPException,
            status_code=409,
            detail="A document with this ID already exists for this developer",
        ),
        asyncpg.NoDataFoundError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified owner does not exist",
        ),
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="Developer or doc owner not found",
        ),
    }
)
@wrap_in_class(
    Doc,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["doc_id"],
        # You could optionally return a computed hash or partial content if desired
    },
)
@increase_counter("create_doc")
@pg_query
@beartype
async def create_doc(
    *,
    developer_id: UUID,
    doc_id: UUID | None = None,
    data: CreateDocRequest,
    owner_type: Literal["user", "agent", "org"] | None = None,
    owner_id: UUID | None = None,
) -> list[tuple[str, list]]:
    """
    Insert a new doc record into Timescale and optionally associate it with an owner.
    """
    # Generate a UUID if not provided
    doc_id = doc_id or uuid7()

    # Create the doc record
    doc_params = [
        developer_id,
        doc_id,
        data.title,
        data.content,
        data.index or 0,  # fallback if no snippet index
        data.modality or "text",
        data.embedding_model or "none",
        data.embedding_dimensions or 0,
        data.language or "english",
        data.metadata or {},
    ]

    queries = [(doc_query, doc_params)]

    # If an owner is specified, associate it:
    if owner_type and owner_id:
        owner_params = [developer_id, doc_id, owner_type, owner_id]
        queries.append((doc_owner_query, owner_params))

    return queries

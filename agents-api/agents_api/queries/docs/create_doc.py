import ast
from typing import Literal
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
        index,
        owner_type,
        owner_id
    )
    VALUES ($1, $2, $3, $4, $5)
    RETURNING doc_id
)
SELECT DISTINCT ON (docs.doc_id)
    docs.doc_id,
    docs.developer_id,
    docs.title,
    array_agg(docs.content ORDER BY docs.index) as content,
    array_agg(docs.index ORDER BY docs.index) as indices,
    docs.modality,
    docs.embedding_model,
    docs.embedding_dimensions,
    docs.language,
    docs.metadata,
    docs.created_at
                        
FROM inserted_owner io
JOIN docs ON docs.doc_id = io.doc_id
GROUP BY 
    docs.doc_id,
    docs.developer_id,
    docs.title,
    docs.modality,
    docs.embedding_model,
    docs.embedding_dimensions,
    docs.language,
    docs.metadata,
    docs.created_at;
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
        "id": d["doc_id"],
        "index": d["indices"][0],
        "content": d["content"][0] if len(d["content"]) == 1 else d["content"],
        **d,
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
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
    modality: Literal["text", "image", "mixed"] | None = "text",
    embedding_model: str | None = "voyage-3",
    embedding_dimensions: int | None = 1024,
    language: str | None = "english",
    index: int | None = 0,
) -> list[tuple[str, list, Literal["fetch", "fetchmany", "fetchrow"]]]:
    """
    Insert a new doc record into Timescale and associate it with an owner.

    Parameters:
        developer_id (UUID): The ID of the developer.
        doc_id (UUID | None): Optional custom UUID for the document. If not provided, one will be generated.
        data (CreateDocRequest): The data for the document.
        owner_type (Literal["user", "agent"]): The type of the owner (required).
        owner_id (UUID): The ID of the owner (required).
        modality (Literal["text", "image", "mixed"]): The modality of the documents.
        embedding_model (str): The model used for embedding.
        embedding_dimensions (int): The dimensions of the embedding.
        language (str): The language of the documents.
        index (int): The index of the documents.

    Returns:
        list[tuple[str, list] | tuple[str, list, str]]: SQL query and parameters for creating the document.
    """
    queries = []
    # Generate a UUID if not provided
    current_doc_id = uuid7() if doc_id is None else doc_id

    # Check if content is a list
    if isinstance(data.content, list):
        final_params_doc = []
        final_params_owner = []
        
        for idx, content in enumerate(data.content):
            doc_params = [
                developer_id,
                current_doc_id,
                data.title,
                content,
                idx,
                modality,
                embedding_model,
                embedding_dimensions,
                language,
                data.metadata or {},
            ]
            final_params_doc.append(doc_params)

            owner_params = [
                developer_id,
                current_doc_id,
                idx,
                owner_type,
                owner_id,
            ]
            final_params_owner.append(owner_params)

        # Add the doc query for each content
        queries.append((doc_query, final_params_doc, "fetchmany"))

        # Add the owner query
        queries.append((doc_owner_query, final_params_owner, "fetchmany"))

    else:

        # Create the doc record
        doc_params = [
            developer_id,
            current_doc_id,
            data.title,
            data.content,
            index,
            modality,
            embedding_model,
            embedding_dimensions,
            language,
            data.metadata or {},
        ]

        owner_params = [
            developer_id,
            current_doc_id,
            index,
            owner_type,
            owner_id,
        ]

        # Add the doc query for single content
        queries.append((doc_query, doc_params, "fetch"))

        # Add the owner query
        queries.append((doc_owner_query, owner_params, "fetch"))

    return queries

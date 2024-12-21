import ast
from typing import Literal
from uuid import UUID

from beartype import beartype
from sqlglot import parse_one

from ...autogen.openapi_model import Doc
from ..utils import pg_query, wrap_in_class

# Update the query to use DISTINCT ON to prevent duplicates
doc_with_embedding_query = parse_one("""
WITH doc_data AS (
    SELECT DISTINCT ON (d.doc_id)
        d.doc_id,
        d.developer_id,
        d.title,
        array_agg(d.content ORDER BY d.index) as content,
        array_agg(d.index ORDER BY d.index) as indices,
        array_agg(e.embedding ORDER BY d.index) as embeddings,
        d.modality,
        d.embedding_model,
        d.embedding_dimensions,
        d.language,
        d.metadata,
        d.created_at
    FROM docs d
    LEFT JOIN docs_embeddings e 
        ON d.doc_id = e.doc_id
    WHERE d.developer_id = $1
        AND d.doc_id = $2
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
SELECT * FROM doc_data;
""").sql(pretty=True)


@wrap_in_class(
    Doc,
    one=True,  # Changed to True since we're now returning one grouped record
    transform=lambda d: {
        "id": d["doc_id"],
        "index": d["indices"][0],
        "content": d["content"][0] if len(d["content"]) == 1 else d["content"],
        "embeddings": d["embeddings"][0] if len(d["embeddings"]) == 1 else d["embeddings"],
        **d,
    },
)
@pg_query
@beartype
async def get_doc(
    *,
    developer_id: UUID,
    doc_id: UUID,
) -> tuple[str, list]:
    """
    Fetch a single doc with its embedding, grouping all content chunks and embeddings.
    
    Parameters:
        developer_id (UUID): The ID of the developer.
        doc_id (UUID): The ID of the document.

    Returns:
        tuple[str, list]: SQL query and parameters for fetching the document.
    """
    return (
        doc_with_embedding_query,
        [developer_id, doc_id],
    )

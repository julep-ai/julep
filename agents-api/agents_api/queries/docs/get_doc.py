import ast
from typing import Literal
from uuid import UUID

from beartype import beartype
from sqlglot import parse_one

from ...autogen.openapi_model import Doc
from ..utils import pg_query, wrap_in_class

# Combined query to fetch document details and embedding
doc_with_embedding_query = parse_one("""
SELECT d.*, e.embedding
FROM docs d
LEFT JOIN doc_owners doc_own 
  ON d.developer_id = doc_own.developer_id 
  AND d.doc_id = doc_own.doc_id
LEFT JOIN docs_embeddings e 
  ON d.doc_id = e.doc_id
WHERE d.developer_id = $1
  AND d.doc_id = $2
  AND (
    ($3::text IS NULL AND $4::uuid IS NULL)
    OR (doc_own.owner_type = $3 AND doc_own.owner_id = $4)
  )
LIMIT 1;
""").sql(pretty=True)


@wrap_in_class(
    Doc,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["doc_id"],
        "content": ast.literal_eval(d["content"])[0]
        if len(ast.literal_eval(d["content"])) == 1
        else ast.literal_eval(d["content"]),
        "embedding": d["embedding"],  # Add embedding to the transformation
    },
)
@pg_query
@beartype
async def get_doc(
    *,
    developer_id: UUID,
    doc_id: UUID,
    owner_type: Literal["user", "agent"] | None = None,
    owner_id: UUID | None = None,
) -> tuple[str, list]:
    """
    Fetch a single doc with its embedding, optionally constrained to a given owner.

    Parameters:
        developer_id (UUID): The ID of the developer.
        doc_id (UUID): The ID of the document.
        owner_type (Literal["user", "agent"]): The type of the owner of the documents.
        owner_id (UUID): The ID of the owner of the documents.

    Returns:
        tuple[str, list]: SQL query and parameters for fetching the document.
    """
    return (
        doc_with_embedding_query,
        [developer_id, doc_id, owner_type, owner_id],
    )

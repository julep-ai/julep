"""
Timescale-based doc embedding search using the `embedding` column.
"""

from typing import List, Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import Doc
from ..utils import pg_query, wrap_in_class

# If you're doing approximate ANN (DiskANN) or IVF, you might use a special function or hint.
# For a basic vector distance search, you can do something like:
search_docs_by_embedding_query = parse_one("""
SELECT d.*,
       (d.embedding <-> $3) AS distance
FROM docs d
LEFT JOIN doc_owners do
  ON d.developer_id = do.developer_id
  AND d.doc_id = do.doc_id
WHERE d.developer_id = $1
  AND (
    ($4::text IS NULL AND $5::uuid IS NULL)
    OR (do.owner_type = $4 AND do.owner_id = $5)
  )
  AND d.embedding IS NOT NULL
ORDER BY d.embedding <-> $3
LIMIT $2;
""").sql(pretty=True)


@wrap_in_class(
    Doc,
    one=False,
    transform=lambda rec: {
        **rec,
        "id": rec["doc_id"],
    },
)
@pg_query
@beartype
async def search_docs_by_embedding(
    *,
    developer_id: UUID,
    query_embedding: List[float],
    k: int = 10,
    owner_type: Literal["user", "agent", "org"] | None = None,
    owner_id: UUID | None = None,
) -> tuple[str, list]:
    """
    Vector-based doc search:
      - developer_id is required
      - query_embedding: the vector to query
      - k: number of results to return
      - owner_type/owner_id: optional doc ownership filter
    """
    if k < 1:
        raise HTTPException(status_code=400, detail="k must be >= 1")

    # Validate embedding length if needed; e.g. 1024 floats
    if not query_embedding:
        raise HTTPException(status_code=400, detail="Empty embedding provided")

    return (
        search_docs_by_embedding_query,
        [developer_id, k, query_embedding, owner_type, owner_id],
    )

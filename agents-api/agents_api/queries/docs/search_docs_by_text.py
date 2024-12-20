"""
Timescale-based doc text search using the `search_tsv` column.
"""

import asyncpg
from typing import Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import Doc
from ..utils import pg_query, wrap_in_class

search_docs_text_query = parse_one("""
SELECT d.*,
       ts_rank_cd(d.search_tsv, websearch_to_tsquery($3)) AS rank
FROM docs d
LEFT JOIN doc_owners do
  ON d.developer_id = do.developer_id
  AND d.doc_id = do.doc_id
WHERE d.developer_id = $1
  AND (
    ($4::text IS NULL AND $5::uuid IS NULL)
    OR (do.owner_type = $4 AND do.owner_id = $5)
  )
  AND d.search_tsv @@ websearch_to_tsquery($3)
ORDER BY rank DESC
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
async def search_docs_by_text(
    *,
    developer_id: UUID,
    query: str,
    k: int = 10,
    owner_type: Literal["user", "agent", "org"] | None = None,
    owner_id: UUID | None = None,
) -> tuple[str, list]:
    """
    Full-text search on docs using the search_tsv column.
      - developer_id: required
      - query: the text to look for
      - k: max results
      - owner_type / owner_id: optional doc ownership filter
    """
    if k < 1:
        raise HTTPException(status_code=400, detail="k must be >= 1")

    return (
        search_docs_text_query,
        [developer_id, k, query, owner_type, owner_id],
    )

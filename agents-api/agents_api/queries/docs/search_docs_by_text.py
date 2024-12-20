"""
Timescale-based doc text search using the `search_tsv` column.
"""

from typing import Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import DocReference
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
    ($4 IS NULL AND $5 IS NULL)
    OR (do.owner_type = $4 AND do.owner_id = $5)
  )
  AND d.search_tsv @@ websearch_to_tsquery($3)
ORDER BY rank DESC
LIMIT $2;
""").sql(pretty=True)


@wrap_in_class(
    DocReference,
    transform=lambda d: {
        "owner": {
            "id": d["owner_id"],
            "role": d["owner_type"],
        },
        "metadata": d.get("metadata", {}),
        **d,
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

    Parameters:
        developer_id (UUID): The ID of the developer.
        query (str): The text to search for.
        k (int): The number of results to return.
        owner_type (Literal["user", "agent", "org"]): The type of the owner of the documents.
        owner_id (UUID): The ID of the owner of the documents.

    Returns:
        tuple[str, list]: SQL query and parameters for searching the documents.
    """
    if k < 1:
        raise HTTPException(status_code=400, detail="k must be >= 1")

    return (
        search_docs_text_query,
        [developer_id, k, query, owner_type, owner_id],
    )

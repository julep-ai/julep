"""
Timescale-based retrieval of a single doc record.
"""
from typing import Literal
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import Doc
from ..utils import pg_query, wrap_in_class

doc_query = parse_one("""
SELECT d.*
FROM docs d
LEFT JOIN doc_owners do ON d.developer_id = do.developer_id AND d.doc_id = do.doc_id
WHERE d.developer_id = $1
  AND d.doc_id = $2
  AND (
    ($3::text IS NULL AND $4::uuid IS NULL)
    OR (do.owner_type = $3 AND do.owner_id = $4)
  )
LIMIT 1;
""").sql(pretty=True)


@wrap_in_class(
    Doc,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["doc_id"],
    },
)
@pg_query
@beartype
async def get_doc(
    *,
    developer_id: UUID,
    doc_id: UUID,
    owner_type: Literal["user", "agent", "org"] | None = None,
    owner_id: UUID | None = None
) -> tuple[str, list]:
    """
    Fetch a single doc, optionally constrained to a given owner.
    """
    return (
        doc_query,
        [developer_id, doc_id, owner_type, owner_id],
    )

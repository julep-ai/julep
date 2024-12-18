from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...common.utils.datetime import utcnow
from ...autogen.openapi_model import ResourceDeletedResponse
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for deleting entries with a developer check
entry_query = parse_one("""
DELETE FROM entries
USING developers
WHERE entries.session_id = $1 -- session_id
AND developers.developer_id = $2     
RETURNING entries.session_id as session_id;
""").sql(pretty=True)

# Define the raw SQL query for deleting entries by entry_ids with a developer check
delete_entry_by_ids_query = parse_one("""
DELETE FROM entries
USING developers
WHERE entries.entry_id = ANY($1) -- entry_ids
AND developers.developer_id = $2 
AND entries.session_id = $3 -- session_id
RETURNING entries.entry_id as entry_id;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: lambda exc: HTTPException(
            status_code=400,
            detail=str(exc),
        ),
        asyncpg.UniqueViolationError: lambda exc: HTTPException(
            status_code=404,
            detail=str(exc),
        ),
    }
)
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": d["session_id"],  # Only return session cleared
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@pg_query
@beartype
async def delete_entries_for_session(
    *,
    developer_id: UUID,
    session_id: UUID,
) -> tuple[str, list]:
    return (
        entry_query,
        [session_id, developer_id],
    )


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=400,
            detail="The specified developer does not exist.",
        ),
        asyncpg.UniqueViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="One or more specified entries do not exist.",
        ),
    }
)
@wrap_in_class(
    ResourceDeletedResponse,
    transform=lambda d: {
        "id": d["entry_id"],
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@pg_query
@beartype
async def delete_entries(
    *, developer_id: UUID, session_id: UUID, entry_ids: list[UUID]
) -> tuple[str, list]:
    return (
        delete_entry_by_ids_query,
        [entry_ids, developer_id, session_id],
    )

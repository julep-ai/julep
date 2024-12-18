from uuid import UUID

from beartype import beartype
from sqlglot import parse_one
import asyncpg
from fastapi import HTTPException

from ...common.protocol.developers import Developer
from ..utils import (
    pg_query,
    wrap_in_class,
    partialclass,
    rewrap_exceptions,
)

# Define the raw SQL query
developer_query = parse_one("""
UPDATE developers 
SET email = $1, active = $2, tags = tags || $3, settings = settings || $4 -- settings
WHERE developer_id = $5 -- developer_id
RETURNING *;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.UniqueViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        )
    }
)
@wrap_in_class(Developer, one=True, transform=lambda d: {**d, "id": d["developer_id"]})
@pg_query
@beartype
async def patch_developer(
    *,
    developer_id: UUID,
    email: str,
    active: bool = True,
    tags: list[str] | None = None,
    settings: dict | None = None,
) -> tuple[str, list]:
    developer_id = str(developer_id)

    return (
        developer_query,
        [email, active, tags or [], settings or {}, developer_id],
    )

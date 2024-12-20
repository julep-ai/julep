from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...common.protocol.developers import Developer
from ..utils import (
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

# Define the raw SQL query
developer_query = parse_one("""
UPDATE developers 
SET email = $1, active = $2, tags = $3, settings = $4
WHERE developer_id = $5
RETURNING *;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        ),
        asyncpg.UniqueViolationError: partialclass(
            HTTPException,
            status_code=409,
            detail="A developer with this email already exists.",
        )
    }
)
@wrap_in_class(Developer, one=True, transform=lambda d: {**d, "id": d["developer_id"]})
@pg_query
@beartype
async def update_developer(
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
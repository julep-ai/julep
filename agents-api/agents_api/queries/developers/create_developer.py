from uuid import UUID

from beartype import beartype
from sqlglot import parse_one
from uuid_extensions import uuid7
import asyncpg
from fastapi import HTTPException

from ...common.protocol.developers import Developer
from ..utils import (
    pg_query,
    wrap_in_class,
    rewrap_exceptions,
    partialclass,
)

# Define the raw SQL query
developer_query = parse_one("""
INSERT INTO developers (
    developer_id,
    email,
    active,
    tags,
    settings
)
VALUES (
    $1, -- developer_id
    $2, -- email
    $3, -- active
    $4, -- tags
    $5::jsonb -- settings
)
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
async def create_developer(
    *,
    email: str,
    active: bool = True,
    tags: list[str] | None = None,
    settings: dict | None = None,
    developer_id: UUID | None = None,
) -> tuple[str, list]:
    developer_id = str(developer_id or uuid7())

    return (
        developer_query,
        [developer_id, email, active, tags or [], settings or {}],
    )
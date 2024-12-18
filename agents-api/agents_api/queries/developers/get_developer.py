"""Module for retrieving document snippets from the CozoDB based on document IDs."""

from typing import Any, TypeVar
from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...common.protocol.developers import Developer
from ..utils import (
    partialclass,
    pg_query,
    wrap_in_class,
    rewrap_exceptions,
)

# TODO: Add verify_developer
verify_developer = None

# Define the raw SQL query
developer_query = parse_one("""
SELECT * FROM developers WHERE developer_id = $1 -- developer_id
""").sql(pretty=True)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


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
async def get_developer(
    *,
    developer_id: UUID,
) -> tuple[str, list]:
    developer_id = str(developer_id)

    return (
        developer_query,
        [developer_id],
    )

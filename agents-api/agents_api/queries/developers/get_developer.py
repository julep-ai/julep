"""Module for retrieving document snippets from the CozoDB based on document IDs."""

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pydantic import ValidationError
from sqlglot import parse_one

from ...common.protocol.developers import Developer
from ..utils import (
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

# TODO: Add verify_developer
verify_developer = None

query = parse_one("SELECT * FROM developers WHERE developer_id = $1").sql(pretty=True)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


# @rewrap_exceptions(
#     {
#         QueryException: partialclass(HTTPException, status_code=403),
#         ValidationError: partialclass(HTTPException, status_code=500),
#     }
# )
@wrap_in_class(Developer, one=True, transform=lambda d: {**d, "id": d["developer_id"]})
@pg_query
@beartype
async def get_developer(
    *,
    developer_id: UUID,
) -> tuple[str, list]:
    developer_id = str(developer_id)

    return (
        query,
        [developer_id],
    )

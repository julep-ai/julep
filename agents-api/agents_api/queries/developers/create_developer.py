from uuid import UUID

from beartype import beartype
from sqlglot import parse_one
from uuid_extensions import uuid7

from ...common.protocol.developers import Developer
from ..utils import (
    pg_query,
    wrap_in_class,
)

query = parse_one("""
INSERT INTO developers (
    developer_id,
    email,
    active,
    tags,
    settings
)
VALUES (
    $1,
    $2,
    $3,
    $4,
    $5::jsonb
)
RETURNING *;
""").sql(pretty=True)


# @rewrap_exceptions(
#     {
#         QueryException: partialclass(HTTPException, status_code=403),
#         ValidationError: partialclass(HTTPException, status_code=500),
#     }
# )
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
        query,
        [developer_id, email, active, tags or [], settings or {}],
    )

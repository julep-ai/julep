from uuid import UUID

from beartype import beartype
from sqlglot import parse_one

from ...common.protocol.developers import Developer
from ..utils import (
    pg_query,
    wrap_in_class,
)

query = parse_one("""
UPDATE developers 
SET email = $1, active = $2, tags = tags || $3, settings = settings || $4
WHERE developer_id = $5
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
        query,
        [email, active, tags or [], settings or {}, developer_id],
    )

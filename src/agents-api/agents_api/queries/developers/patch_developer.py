from uuid import UUID

from beartype import beartype

from ...common.protocol.developers import Developer
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
developer_query = """
UPDATE developers
SET email = $1, active = $2, tags = tags || $3, settings = settings || $4 -- settings
WHERE developer_id = $5 -- developer_id
RETURNING *;
"""


@rewrap_exceptions(common_db_exceptions("developer", ["patch"]))
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

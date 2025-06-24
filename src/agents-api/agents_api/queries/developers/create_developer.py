from uuid import UUID

from beartype import beartype
from uuid_extensions import uuid7

from ...common.protocol.developers import Developer
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query
developer_query = """
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
"""


@rewrap_exceptions(common_db_exceptions("developer", ["create"]))
@wrap_in_class(
    Developer,
    one=True,
    transform=lambda d: {**d, "id": d["developer_id"]},
)
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

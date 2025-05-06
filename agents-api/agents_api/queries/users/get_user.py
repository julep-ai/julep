from typing import Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import User
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
user_query = """
SELECT
    u.user_id as id, -- user_id
    u.developer_id, -- developer_id
    u.name, -- name
    u.about, -- about
    u.metadata, -- metadata
    u.created_at, -- created_at
    u.updated_at, -- updated_at
    p.canonical_name AS project -- project
FROM users u
LEFT JOIN projects p ON u.project_id = p.project_id
WHERE u.developer_id = $1
AND u.user_id = $2;
"""


@rewrap_exceptions(common_db_exceptions("user", ["get"]))
@wrap_in_class(User, one=True)
@pg_query
@beartype
async def get_user(
    *,
    developer_id: UUID,
    user_id: UUID,
) -> tuple[str, list, Literal["fetchrow", "fetchmany", "fetch"]]:
    """
    Constructs an optimized SQL query to retrieve a user's details.
    Uses the primary key index (developer_id, user_id) for efficient lookup.

    Args:
        developer_id (UUID): The UUID of the developer.
        user_id (UUID): The UUID of the user to retrieve.

    Returns:
        tuple[str, list, str]: SQL query, parameters, and fetch mode.
    """

    return (
        user_query,
        [developer_id, user_id],
        "fetchrow",
    )

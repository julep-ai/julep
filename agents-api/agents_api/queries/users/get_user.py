from typing import Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import User
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
user_query = """
SELECT
    user_id as id, -- user_id
    developer_id, -- developer_id
    name, -- name
    about, -- about
    metadata, -- metadata
    created_at, -- created_at
    updated_at -- updated_at
FROM users
WHERE developer_id = $1
AND user_id = $2;
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

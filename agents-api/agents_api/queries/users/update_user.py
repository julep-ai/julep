from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import UpdateUserRequest, User
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import increase_counter
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
user_query = """
UPDATE users
SET
    name = $3, -- name
    about = $4, -- about
    metadata = $5 -- metadata
WHERE developer_id = $1 -- developer_id
AND user_id = $2 -- user_id
RETURNING *
"""


@rewrap_exceptions(common_db_exceptions("user", ["update"]))
@wrap_in_class(
    User,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["user_id"],
    },
)
@increase_counter("update_user")
@pg_query
@beartype
async def update_user(
    *, developer_id: UUID, user_id: UUID, data: UpdateUserRequest
) -> tuple[str, list]:
    """
    Constructs an optimized SQL query to update a user's details.
    Uses primary key for efficient update.

    Args:
        developer_id (UUID): The developer's UUID
        user_id (UUID): The user's UUID
        data (UpdateUserRequest): Updated user data

    Returns:
        tuple[str, list]: SQL query and parameters
    """
    params = [
        developer_id,
        user_id,
        data.name,
        data.about,
        data.metadata or {},
    ]

    return (
        user_query,
        params,
    )

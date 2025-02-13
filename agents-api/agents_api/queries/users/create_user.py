from uuid import UUID

from beartype import beartype
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateUserRequest, User
from ...common.utils.db_exceptions import common_db_exceptions
from ...metrics.counters import query_metrics
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
user_query = """
INSERT INTO users (
    developer_id,
    user_id,
    name,
    about,
    metadata
)
VALUES (
    $1, -- developer_id
    $2, -- user_id
    $3, -- name
    $4, -- about
    $5::jsonb -- metadata
)
RETURNING *;
"""


@rewrap_exceptions(common_db_exceptions("user", ["create"]))
@wrap_in_class(
    User,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["user_id"],
    },
)
@query_metrics("create_user")
@pg_query
@beartype
async def create_user(
    *,
    developer_id: UUID,
    user_id: UUID | None = None,
    data: CreateUserRequest,
) -> tuple[str, list]:
    """
    Constructs the SQL query to create a new user.

    Args:
        developer_id (UUID): The UUID of the developer creating the user.
        user_id (UUID, optional): The UUID for the new user. If None, one will be generated.
        data (CreateUserRequest): The user data to insert.

    Returns:
        tuple[str, list]: A tuple containing the SQL query and its parameters.
    """
    user_id = user_id or uuid7()
    metadata = data.metadata or {}

    params = [
        developer_id,  # $1
        user_id,  # $2
        data.name,  # $3
        data.about,  # $4
        metadata,  # $5
    ]

    return (
        user_query,
        params,
    )

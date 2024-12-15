from typing import Any
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from psycopg import errors as psycopg_errors
from sqlglot import parse_one

from ...autogen.openapi_model import ResourceDeletedResponse
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

@rewrap_exceptions({
    psycopg_errors.ForeignKeyViolation: partialclass(
        HTTPException,
        status_code=404,
        detail="The specified developer does not exist.",
    )
})
@wrap_in_class(ResourceDeletedResponse, one=True)
@increase_counter("delete_user")
@pg_query
@beartype
def delete_user_query(*, developer_id: UUID, user_id: UUID) -> tuple[list[str], dict]:
    """
    Constructs optimized SQL queries to delete a user and related data.
    Uses primary key for efficient deletion.

    Args:
        developer_id (UUID): The developer's UUID
        user_id (UUID): The user's UUID

    Returns:
        tuple[list[str], dict]: List of SQL queries and parameters
    """
    query = parse_one("""
    BEGIN;
    DELETE FROM user_files WHERE developer_id = %(developer_id)s AND user_id = %(user_id)s;
    DELETE FROM user_docs WHERE developer_id = %(developer_id)s AND user_id = %(user_id)s;
    DELETE FROM users WHERE developer_id = %(developer_id)s AND user_id = %(user_id)s
    RETURNING user_id as id, developer_id;
    COMMIT;
    """).sql()

    return [query], {"developer_id": developer_id, "user_id": user_id}
from typing import Any
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from psycopg import errors as psycopg_errors
from sqlglot import parse_one
from pydantic import ValidationError
from uuid_extensions import uuid7

from ...autogen.openapi_model import CreateUserRequest, User
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

@rewrap_exceptions({
    psycopg_errors.ForeignKeyViolation: partialclass(
        HTTPException,
        status_code=404,
        detail="The specified developer does not exist.",
    ),
    ValidationError: partialclass(
        HTTPException,
        status_code=400,
        detail="Input validation failed. Please check the provided data.",
    ),
})
@wrap_in_class(User)
@increase_counter("create_user")
@pg_query
@beartype
def create_user(
    *,
    developer_id: UUID,
    user_id: UUID | None = None,
    data: CreateUserRequest,
) -> tuple[str, dict]:
    """
    Constructs the SQL query to create a new user.

    Args:
        developer_id (UUID): The UUID of the developer creating the user.
        user_id (UUID, optional): The UUID for the new user. If None, one will be generated.
        data (CreateUserRequest): The user data to insert.

    Returns:
        tuple[str, dict]: A tuple containing the SQL query and its parameters.
    """
    user_id = user_id or uuid7()
    
    query = parse_one("""
    INSERT INTO users (
        developer_id,
        user_id,
        name,
        about,
        metadata
    )
    VALUES (
        %(developer_id)s,
        %(user_id)s,
        %(name)s,
        %(about)s,
        %(metadata)s
    )
    RETURNING *;
    """).sql()

    params = {
        "developer_id": developer_id,
        "user_id": user_id,
        "name": data.name,
        "about": data.about,
        "metadata": data.metadata or {},
    }

    return query, params

from typing import Any
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from psycopg import errors as psycopg_errors
from sqlglot import parse_one

from ...autogen.openapi_model import PatchUserRequest, ResourceUpdatedResponse
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

@rewrap_exceptions({
    psycopg_errors.ForeignKeyViolation: partialclass(
        HTTPException,
        status_code=404,
        detail="The specified developer does not exist.",
    )
})
@wrap_in_class(ResourceUpdatedResponse, one=True)
@increase_counter("patch_user")
@pg_query
@beartype
def patch_user_query(
    *, 
    developer_id: UUID, 
    user_id: UUID, 
    data: PatchUserRequest
) -> tuple[str, dict]:
    """
    Constructs an optimized SQL query for partial user updates.
    Uses primary key for efficient update and jsonb_merge for metadata.

    Args:
        developer_id (UUID): The developer's UUID
        user_id (UUID): The user's UUID
        data (PatchUserRequest): Partial update data

    Returns:
        tuple[str, dict]: SQL query and parameters
    """
    update_parts = []
    params = {
        "developer_id": developer_id,
        "user_id": user_id,
    }

    if data.name is not None:
        update_parts.append("name = %(name)s")
        params["name"] = data.name
    if data.about is not None:
        update_parts.append("about = %(about)s")
        params["about"] = data.about
    if data.metadata is not None:
        update_parts.append("metadata = metadata || %(metadata)s")
        params["metadata"] = data.metadata

    query = parse_one(f"""
    UPDATE users
    SET {", ".join(update_parts)}
    WHERE developer_id = %(developer_id)s 
    AND user_id = %(user_id)s
    RETURNING 
        user_id as id,
        developer_id,
        name,
        about,
        metadata,
        created_at,
        updated_at;
    """).sql()

    return query, params
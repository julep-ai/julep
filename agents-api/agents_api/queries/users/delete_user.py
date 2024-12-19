from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query outside the function
delete_query = parse_one("""
WITH deleted_file_owners AS (
    DELETE FROM file_owners
    WHERE developer_id = $1 
    AND owner_type = 'user'
    AND owner_id = $2
),
deleted_doc_owners AS (
    DELETE FROM doc_owners
    WHERE developer_id = $1
    AND owner_type = 'user'
    AND owner_id = $2
),
deleted_files AS (
    DELETE FROM files
    WHERE developer_id = $1
    AND file_id IN (
        SELECT file_id FROM file_owners 
        WHERE developer_id = $1 
        AND owner_type = 'user' 
        AND owner_id = $2
    )
),
deleted_docs AS (
    DELETE FROM docs
    WHERE developer_id = $1
    AND doc_id IN (
        SELECT doc_id FROM doc_owners
        WHERE developer_id = $1 
        AND owner_type = 'user' 
        AND owner_id = $2
    )
)
DELETE FROM users 
WHERE developer_id = $1 AND user_id = $2
RETURNING user_id, developer_id;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        ),
        asyncpg.UniqueViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified user does not exist.",
        ),
    }
)
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["user_id"],
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@pg_query
@beartype
async def delete_user(*, developer_id: UUID, user_id: UUID) -> tuple[str, list]:
    """
    Constructs optimized SQL query to delete a user and related data.
    Uses primary key for efficient deletion.

    Args:
        developer_id (UUID): The developer's UUID
        user_id (UUID): The user's UUID

    Returns:
        tuple[str, list]: SQL query and parameters
    """

    return (
        delete_query,
        [developer_id, user_id],
    )

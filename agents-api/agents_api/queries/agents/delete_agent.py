"""
This module contains the functionality for deleting agents from the PostgreSQL database.
It constructs and executes SQL queries to remove agent records and associated data.
"""

from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ..utils import (
    partialclass,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)

# Define the raw SQL query
agent_query = parse_one("""
WITH deleted_file_owners AS (
    DELETE FROM file_owners
    WHERE developer_id = $1 
    AND owner_type = 'agent'
    AND owner_id = $2
),
deleted_doc_owners AS (
    DELETE FROM doc_owners
    WHERE developer_id = $1
    AND owner_type = 'agent'
    AND owner_id = $2
),
deleted_files AS (
    DELETE FROM files
    WHERE developer_id = $1
    AND file_id IN (
        SELECT file_id FROM file_owners 
        WHERE developer_id = $1 
        AND owner_type = 'agent' 
        AND owner_id = $2
    )
),
deleted_docs AS (
    DELETE FROM docs
    WHERE developer_id = $1
    AND doc_id IN (
        SELECT doc_id FROM doc_owners
        WHERE developer_id = $1 
        AND owner_type = 'agent' 
        AND owner_id = $2
    )
),
deleted_tools AS (
    DELETE FROM tools
    WHERE agent_id = $2 AND developer_id = $1
)
DELETE FROM agents 
WHERE agent_id = $2 AND developer_id = $1
RETURNING developer_id, agent_id;
""").sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.exceptions.ForeignKeyViolationError: partialclass(
            HTTPException,
            status_code=404,
            detail="The specified developer does not exist.",
        ),
        asyncpg.exceptions.UniqueViolationError: partialclass(
            HTTPException,
            status_code=409,
            detail="An agent with this canonical name already exists for this developer.",
        ),
        asyncpg.exceptions.CheckViolationError: partialclass(
            HTTPException,
            status_code=400,
            detail="The provided data violates one or more constraints. Please check the input values.",
        ),
        asyncpg.exceptions.DataError: partialclass(
            HTTPException,
            status_code=400,
            detail="Invalid data provided. Please check the input values.",
        ),
    }
)
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {**d, "id": d["agent_id"], "deleted_at": utcnow()},
)
@pg_query
@beartype
async def delete_agent(*, agent_id: UUID, developer_id: UUID) -> tuple[str, list]:
    """
    Constructs the SQL query to delete an agent and its related settings.

    Args:
        agent_id (UUID): The UUID of the agent to be deleted.
        developer_id (UUID): The UUID of the developer owning the agent.

    Returns:
        tuple[str, list]: A tuple containing the SQL query and its parameters.
    """
    # Note: We swap the parameter order because the queries use $1 for developer_id and $2 for agent_id
    params = [developer_id, agent_id]

    return (
        agent_query,
        params,
    )

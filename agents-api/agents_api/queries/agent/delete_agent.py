"""
This module contains the functionality for deleting agents from the PostgreSQL database.
It constructs and executes SQL queries to remove agent records and associated data.
"""

from typing import Any, TypeVar
from uuid import UUID

from fastapi import HTTPException
from ...metrics.counters import increase_counter
from ..utils import (
    pg_query,
    partialclass,
    rewrap_exceptions,
    wrap_in_class,
)
from beartype import beartype
from psycopg import errors as psycopg_errors
from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

@rewrap_exceptions(
    {
        psycopg_errors.ForeignKeyViolation: partialclass(
            HTTPException, 
            status_code=404,
            detail="The specified developer does not exist."
        )
    }
    # TODO: Add more exceptions
)
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": UUID(d.pop("agent_id")),
        "deleted_at": utcnow(),
        "jobs": [],
    },
    _kind="deleted",
)
@pg_query
@increase_counter("delete_agent")
@beartype
def delete_agent_query(*, agent_id: UUID, developer_id: UUID) -> tuple[list[str], dict]:
    """
    Constructs the SQL queries to delete an agent and its related settings.

    Args:
        agent_id (UUID): The UUID of the agent to be deleted.
        developer_id (UUID): The UUID of the developer owning the agent.

    Returns:
        tuple[list[str], dict]: A tuple containing the list of SQL queries and their parameters.
    """

    queries = [
        """
        -- Delete docs that were only associated with this agent
        DELETE FROM docs
        WHERE developer_id = %(developer_id)s
        AND doc_id IN (
            SELECT ad.doc_id
            FROM agent_docs ad
            WHERE ad.agent_id = %(agent_id)s
            AND ad.developer_id = %(developer_id)s
        );
        """,
        """
        -- Delete agent_docs entries
        DELETE FROM agent_docs
        WHERE agent_id = %(agent_id)s AND developer_id = %(developer_id)s;
        """,
        """
        -- Delete tools related to the agent
        DELETE FROM tools
        WHERE agent_id = %(agent_id)s AND developer_id = %(developer_id)s;
        """,
        """
        -- Delete the agent
        DELETE FROM agents
        WHERE agent_id = %(agent_id)s AND developer_id = %(developer_id)s;
        """
    ]

    params = {
        "agent_id": agent_id,
        "developer_id": developer_id,
    }

    return (queries, params)

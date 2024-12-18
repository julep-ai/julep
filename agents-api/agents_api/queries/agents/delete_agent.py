"""
This module contains the functionality for deleting agents from the PostgreSQL database.
It constructs and executes SQL queries to remove agent records and associated data.
"""

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from sqlglot import parse_one

from ...autogen.openapi_model import ResourceDeletedResponse
from ...metrics.counters import increase_counter
from ...common.utils.datetime import utcnow
from ..utils import (
    pg_query,
    wrap_in_class,
    rewrap_exceptions,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")

raw_query = """
WITH deleted_docs AS (
    DELETE FROM docs
    WHERE developer_id = $1
    AND doc_id IN (
        SELECT ad.doc_id
        FROM agent_docs ad
        WHERE ad.agent_id = $2
        AND ad.developer_id = $1
    )
), deleted_agent_docs AS (
    DELETE FROM agent_docs
    WHERE agent_id = $2 AND developer_id = $1
), deleted_tools AS (
    DELETE FROM tools
    WHERE agent_id = $2 AND developer_id = $1
)
DELETE FROM agents 
WHERE agent_id = $2 AND developer_id = $1
RETURNING developer_id, agent_id;
"""


# Convert the list of queries into a single query string
query = parse_one(raw_query).sql(pretty=True)


# @rewrap_exceptions(
#     {
#         psycopg_errors.ForeignKeyViolation: partialclass(
#             HTTPException,
#             status_code=404,
#             detail="The specified developer does not exist.",
#         )
#     }
#     # TODO: Add more exceptions
# )
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {**d, "id": d["agent_id"], "deleted_at": utcnow()},
)
@increase_counter("delete_agent")
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

    return (query, params)

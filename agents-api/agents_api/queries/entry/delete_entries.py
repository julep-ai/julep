from uuid import UUID

import asyncpg
from beartype import beartype
from fastapi import HTTPException
from sqlglot import parse_one
from sqlglot.optimizer import optimize

from ...autogen.openapi_model import ResourceDeletedResponse
from ...metrics.counters import increase_counter
from ..utils import partialclass, pg_query, rewrap_exceptions, wrap_in_class

# Define the raw SQL query for deleting entries
raw_query = """
DELETE FROM entries
WHERE session_id = $1
RETURNING session_id as id;
"""

# Parse and optimize the query
query = optimize(
    parse_one(raw_query),
    schema={
        "entries": {
            "session_id": "UUID",
        }
    },
).sql(pretty=True)


@rewrap_exceptions(
    {
        asyncpg.ForeignKeyViolationError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(ResourceDeletedResponse, one=True)
@increase_counter("delete_entries_for_session")
@pg_query
@beartype
def delete_entries_for_session(
    *, developer_id: UUID, session_id: UUID, mark_session_as_updated: bool = True
) -> tuple[str, dict]:
    return (
        query,
        [session_id],
    )

from typing import Literal
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import CreateEntryRequest, Entry
from ...common.utils.cozo import cozo_process_mutate_data
from ...common.utils.datetime import utcnow
from ...common.utils.messages import content_to_json
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    Entry,
    transform=lambda d: {
        "id": UUID(d.pop("entry_id")),
        **d,
    },
)
@cozo_query
@beartype
def list_entries(
    *,
    developer_id: UUID,
    session_id: UUID,
    limit: int = 100,
    allowed_sources: list[str] = ["api_request", "api_response"],
) -> tuple[str, dict]:
    """
    Constructs and executes a query to retrieve entries from the 'cozodb' database.

    Parameters:
        session_id (UUID): The session ID to filter entries.
        limit (int): The maximum number of entries to return. Defaults to 100.
        offset (int): The offset from which to start returning entries. Defaults to 0.

    """
    developer_id = str(developer_id)
    session_id = str(session_id)

    list_query = """
        ?[
            session_id,
            entry_id,
            role,
            name,
            content,
            source,
            token_count,
            created_at,
            timestamp,
        ] := *entries{
            session_id,
            entry_id,
            role,
            name,
            content,
            source,
            token_count,
            created_at,
            timestamp,
        },
        source in $allowed_sources,
        session_id = to_uuid($session_id),

        :sort timestamp
    """

    if limit > 0:
        list_query += f"\n:limit {limit}"

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "sessions", session_id=session_id
        ),
        list_query,
    ]

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return (query, {"session_id": session_id, "allowed_sources": allowed_sources})

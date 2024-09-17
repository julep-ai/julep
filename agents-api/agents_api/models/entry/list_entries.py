from typing import Any, Literal, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import Entry
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(Entry)
@cozo_query
@beartype
def list_entries(
    *,
    developer_id: UUID,
    session_id: UUID,
    allowed_sources: list[str] = ["api_request", "api_response"],
    limit: int = -1,
    offset: int = 0,
    sort_by: Literal["created_at", "timestamp"] = "timestamp",
    direction: Literal["asc", "desc"] = "asc",
    exclude_relations: list[str] = [],
) -> tuple[list[str], dict]:
    """
    Constructs and executes a query to retrieve entries from the 'cozodb' database.
    """

    developer_id = str(developer_id)
    session_id = str(session_id)

    sort = f"{'-' if direction == 'desc' else ''}{sort_by}"

    exclude_relations_query = """
        not *relations {
            relation,
            tail: id,
        },
        relation in $exclude_relations,
        # !is_in(relation, $exclude_relations),
    """

    list_query = f"""
        ?[
            session_id,
            id,
            role,
            name,
            content,
            source,
            token_count,
            tokenizer,
            created_at,
            timestamp,
        ] := *entries {{
            session_id,
            entry_id: id,
            role,
            name,
            content,
            source,
            token_count,
            tokenizer,
            created_at,
            timestamp,
        }},
        {exclude_relations_query if exclude_relations else ''}
        source in $allowed_sources,
        session_id = to_uuid($session_id),

        :sort {sort}
    """

    if limit > 0:
        list_query += f"\n:limit {limit}"
        list_query += f"\n:offset {offset}"

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "sessions", session_id=session_id
        ),
        list_query,
    ]

    return (
        queries,
        {
            "session_id": session_id,
            "allowed_sources": allowed_sources,
            "exclude_relations": exclude_relations,
        },
    )

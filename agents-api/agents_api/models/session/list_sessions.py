"""This module contains functions for querying session data from the 'cozodb' database."""

from typing import Any, Literal, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...common.protocol.sessions import make_session
from ...common.utils import json
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
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
@wrap_in_class(make_session)
@cozo_query
@beartype
def list_sessions(
    *,
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict[str, Any] = {},
) -> tuple[list[str], dict]:
    """
    Lists sessions from the 'cozodb' database based on the provided filters.

    Parameters:
        developer_id (UUID): The developer's ID to filter sessions by.
        limit (int): The maximum number of sessions to return.
        offset (int): The offset from which to start listing sessions.
        metadata_filter (dict[str, Any]): A dictionary of metadata fields to filter sessions by.
    """
    metadata_filter_str = ", ".join(
        [
            f"metadata->{json.dumps(k)} == {json.dumps(v)}"
            for k, v in metadata_filter.items()
        ]
    )

    sort = f"{'-' if direction == 'desc' else ''}{sort_by}"

    list_query = f"""
        input[developer_id] <- [[
            to_uuid($developer_id),
        ]]

        participants[collect(participant_id), participant_type, session_id] :=
            *session_lookup{{
                session_id,
                participant_id,
                participant_type,
            }}

        # We have to do this dance because users can be zero or more
        users_p[users, session_id] :=
            participants[users, "user", session_id]

        users_p[users, session_id] :=
            not participants[_, "user", session_id],
            users = []

        ?[
            agents,
            users,
            id,
            situation,
            summary,
            updated_at,
            created_at,
            metadata,
            token_budget,
            context_overflow,
        ] :=
            input[developer_id],
            *sessions{{
                developer_id,
                session_id: id,
                situation,
                summary,
                created_at,
                updated_at: validity,
                metadata,
                token_budget,
                context_overflow,
                @ "END"
            }},
            users_p[users, id],
            participants[agents, "agent", id],
            updated_at = to_int(validity),
            {metadata_filter_str}

        :limit $limit
        :offset $offset
        :sort {sort}
    """

    # Datalog query to retrieve agent information based on filters, sorted by creation date in descending order.
    queries = [
        verify_developer_id_query(developer_id),
        list_query,
    ]

    # Execute the datalog query and return the results as a pandas DataFrame.
    return (
        queries,
        {"developer_id": str(developer_id), "limit": limit, "offset": offset},
    )

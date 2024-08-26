"""This module contains the implementation for deleting sessions from the 'cozodb' database using datalog queries."""

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
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
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": UUID(d.pop("session_id")),
        "deleted_at": utcnow(),
        "jobs": [],
    },
    _kind="deleted",
)
@cozo_query
@beartype
def delete_session(
    *,
    developer_id: UUID,
    session_id: UUID,
) -> tuple[list[str], dict]:
    """
    Deletes a session and its related data from the 'cozodb' database.

    Parameters:
    - developer_id (UUID): The unique identifier for the developer.
    - session_id (UUID): The unique identifier for the session to be deleted.

    Returns:
    - ResourceDeletedResponse: The response indicating the deletion of the session.
    """
    session_id = str(session_id)
    developer_id = str(developer_id)

    # Constructs and executes a datalog query to delete the specified session and its associated data based on the session_id and developer_id.
    delete_lookup_query = """
        # Convert session_id to UUID format
        input[session_id] <- [[
            to_uuid($session_id),
        ]]

        # Select sessions based on the session_id provided
        ?[
            session_id,
            participant_id,
            participant_type,
        ] :=
            input[session_id],
            *session_lookup{
                session_id,
                participant_id,
                participant_type,
            }

        # Delete entries from session_lookup table matching the criteria
        :delete session_lookup {
            session_id,
            participant_id,
            participant_type,
        }
    """

    delete_query = """
        # Convert developer_id and session_id to UUID format
        input[developer_id, session_id] <- [[
            to_uuid($developer_id),
            to_uuid($session_id),
        ]]

        # Select sessions based on the developer_id and session_id provided
        ?[developer_id, session_id, updated_at] :=
            input[developer_id, session_id],
            *sessions {
                developer_id, 
                session_id,
                updated_at,
            }

        # Delete entries from sessions table matching the criteria
        :delete sessions {
            developer_id,
            session_id,
            updated_at,
        }
        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "sessions", session_id=session_id
        ),
        delete_lookup_query,
        delete_query,
    ]

    return (queries, {"session_id": session_id, "developer_id": developer_id})

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
    mark_session_updated_query,
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
        IndexError: partialclass(HTTPException, status_code=404),
    }
)
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": UUID(d.pop("session_id")),  # Only return session cleared
        "deleted_at": utcnow(),
        "jobs": [],
    },
    _kind="deleted",
)
@cozo_query
@beartype
def delete_entries_for_session(
    *, developer_id: UUID, session_id: UUID, mark_session_as_updated: bool = True
) -> tuple[list[str], dict]:
    """
    Constructs and returns a datalog query for deleting entries associated with a given session ID from the 'cozodb' database.

    Parameters:
    - session_id (UUID): The unique identifier of the session whose entries are to be deleted.
    """

    delete_query = """
        input[session_id] <- [[
            to_uuid($session_id),
        ]]

        ?[
            session_id,
            entry_id,
            source,
            role,
        ] := input[session_id],
            *entries{
                session_id,
                entry_id,
                source,
                role,
            }
        
        :delete entries {
            session_id,
            entry_id,
            source,
            role,
        }

        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "sessions", session_id=session_id
        ),
        mark_session_updated_query(developer_id, session_id)
        if mark_session_as_updated
        else "",
        delete_query,
    ]

    return (queries, {"session_id": str(session_id)})


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    ResourceDeletedResponse,
    transform=lambda d: {
        "id": UUID(d.pop("entry_id")),
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@cozo_query
@beartype
def delete_entries(
    *, developer_id: UUID, session_id: UUID, entry_ids: list[UUID]
) -> tuple[list[str], dict]:
    delete_query = """
        input[entry_id_str] <- $entry_ids
        
        ?[
            entry_id,
            session_id,
            source,
            role,
        ] :=
            input[entry_id_str],
            entry_id = to_uuid(entry_id_str),
            *entries {
                session_id,
                entry_id,
                source,
                role,
            }

        :delete entries {
            session_id,
            entry_id,
            source,
            role,
        }

        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "sessions", session_id=session_id
        ),
        delete_query,
    ]

    return (queries, {"entry_ids": [[str(id)] for id in entry_ids]})

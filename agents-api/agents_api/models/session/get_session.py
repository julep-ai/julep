from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import make_session
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
@wrap_in_class(make_session, one=True)
@cozo_query
@beartype
def get_session(
    *,
    developer_id: UUID,
    session_id: UUID,
) -> tuple[list[str], dict]:
    """
    Constructs and executes a datalog query to retrieve session information from the 'cozodb' database.

    Parameters:
        developer_id (UUID): The developer's unique identifier.
        session_id (UUID): The session's unique identifier.
    """
    session_id = str(session_id)
    developer_id = str(developer_id)

    # This query retrieves session information by using `input` to pass parameters,
    get_query = """
    input[developer_id, session_id] <- [[
        to_uuid($developer_id),
        to_uuid($session_id),
    ]]

    participants[collect(participant_id), participant_type] :=
        input[_, session_id],
        *session_lookup{
            session_id,
            participant_id,
            participant_type,
        }

    # We have to do this dance because users can be zero or more
    users_p[users] :=
        participants[users, "user"]

    users_p[users] :=
        not participants[_, "user"],
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
        render_templates,
        token_budget,
        context_overflow,
    ] := input[developer_id, id],
        users_p[users],
        participants[agents, "agent"],
        *sessions{
            developer_id,
            session_id: id,
            situation,
            summary,
            created_at,
            updated_at: validity,
            metadata,
            render_templates,
            token_budget,
            context_overflow,
            @ "NOW"
        }, updated_at = to_int(validity)
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, "sessions", session_id=session_id
        ),
        get_query,
    ]

    return (queries, {"session_id": session_id, "developer_id": developer_id})

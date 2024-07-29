from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import User
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
@wrap_in_class(User, one=True)
@cozo_query
@beartype
def get_user(
    *,
    developer_id: UUID,
    user_id: UUID,
) -> tuple[str, dict]:
    # Convert UUIDs to strings for query compatibility.
    user_id = str(user_id)
    developer_id = str(developer_id)

    get_query = """
    input[developer_id, user_id] <- [[to_uuid($developer_id), to_uuid($user_id)]]

    ?[
        id,
        name,
        about,
        created_at,
        updated_at,
        metadata,
    ] := input[developer_id, id],
        *users {
            user_id: id,
            developer_id,
            name,
            about,
            created_at,
            updated_at,
            metadata,
        }"""

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "users", user_id=user_id),
        get_query,
    ]

    query = "}\n\n{\n".join(queries)
    query = f"{{ {query} }}"

    return (query, {"developer_id": developer_id, "user_id": user_id})

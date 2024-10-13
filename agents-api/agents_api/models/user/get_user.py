from typing import Any, TypeVar
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

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions(
    {
        lambda e: isinstance(e, QueryException)
        and "Developer does not exist" in str(e): lambda *_: HTTPException(
            detail="The specified developer does not exist.",
            status_code=403,
        ),
        lambda e: isinstance(e, QueryException)
        and "Developer does not own resource"
        in e.resp["display"]: lambda *_: HTTPException(
            detail="The specified developer does not own the requested resource. Please verify the ownership or check if the developer ID is correct.",
            status_code=404,
        ),
        QueryException: partialclass(
            HTTPException,
            status_code=400,
            detail="A database query failed to return the expected results. This might occur if the requested resource doesn't exist or your query parameters are incorrect.",
        ),
        ValidationError: partialclass(
            HTTPException,
            status_code=400,
            detail="Input validation failed. Please check the provided data for missing or incorrect fields, and ensure it matches the required format.",
        ),
        TypeError: partialclass(
            HTTPException,
            status_code=400,
            detail="A type mismatch occurred. This likely means the data provided is of an incorrect type (e.g., string instead of integer). Please review the input and try again.",
        ),
    }
)
@wrap_in_class(User, one=True)
@cozo_query
@beartype
def get_user(
    *,
    developer_id: UUID,
    user_id: UUID,
) -> tuple[list[str], dict]:
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
        }

    :limit 1
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "users", user_id=user_id),
        get_query,
    ]

    return (queries, {"developer_id": developer_id, "user_id": user_id})

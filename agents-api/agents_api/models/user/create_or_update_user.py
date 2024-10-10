"""
This module contains the functionality for creating users in the CozoDB database.
It includes functions to construct and execute datalog queries for inserting new user records.
"""

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import CreateOrUpdateUserRequest, User
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
@wrap_in_class(User, one=True, transform=lambda d: {"id": UUID(d.pop("user_id")), **d})
@cozo_query
@beartype
def create_or_update_user(
    *,
    developer_id: UUID,
    user_id: UUID,
    data: CreateOrUpdateUserRequest,
) -> tuple[list[str], dict]:
    """
    Constructs and executes a datalog query to create a new user in the database.

    Parameters:
        user_id (UUID): The unique identifier for the user.
        developer_id (UUID): The unique identifier for the developer creating the user.
        name (str): The name of the user.
        about (str): A description of the user.
        metadata (dict, optional): A dictionary of metadata for the user. Defaults to an empty dict.
        client (CozoClient, optional): The CozoDB client instance to use for the query. Defaults to a preconfigured client instance.

    Returns:
        User: The newly created user record.
    """

    # Extract the user data from the payload
    data.metadata = data.metadata or {}

    user_data = data.model_dump()

    # Create the user
    # Construct a query to insert the new user record into the users table
    user_query = """
        input[user_id, developer_id, name, about, metadata, updated_at] <- [
            [$user_id, $developer_id, $name, $about, $metadata, now()]
        ]

        ?[user_id, developer_id, name, about, metadata, created_at, updated_at] :=
            input[_user_id, developer_id, name, about, metadata, updated_at],
            *users{
                developer_id,
                user_id,
                created_at,
            },
            user_id = to_uuid(_user_id),

        ?[user_id, developer_id, name, about, metadata, created_at, updated_at] :=
            input[_user_id, developer_id, name, about, metadata, updated_at],
            not *users{
                developer_id,
                user_id,
            }, created_at = now(),
            user_id = to_uuid(_user_id),

        :put users {
            developer_id,
            user_id =>
            name,
            about,
            metadata,
            created_at,
            updated_at,
        }
        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        user_query,
    ]

    return (
        queries,
        {
            "user_id": str(user_id),
            "developer_id": str(developer_id),
            **user_data,
        },
    )

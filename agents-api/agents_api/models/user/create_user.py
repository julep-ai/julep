"""
This module contains the functionality for creating a new user in the CozoDB database.
It defines a query for inserting user data into the 'users' relation.
"""

from typing import Any, TypeVar
from uuid import UUID, uuid4

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import CreateUserRequest, User
from ...metrics.counters import increase_counter
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
        lambda e: isinstance(e, QueryException)
        and "asserted to return some results, but returned none"
        in str(e): lambda *_: HTTPException(
            detail="Developer not found. Please ensure the provided auth token (which refers to your developer_id) is valid and the developer has the necessary permissions to create an agent.",
            status_code=403,
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
@wrap_in_class(
    User,
    one=True,
    transform=lambda d: {"id": UUID(d.pop("user_id")), **d},
    _kind="inserted",
)
@cozo_query
@increase_counter("create_user")
@beartype
def create_user(
    *,
    developer_id: UUID,
    user_id: UUID | None = None,
    data: CreateUserRequest,
) -> tuple[list[str], dict]:
    """
    Constructs and executes a datalog query to create a new user in the CozoDB database.

    Parameters:
        user_id (UUID): The unique identifier for the user.
        developer_id (UUID): The unique identifier for the developer creating the user.
        name (str): The name of the user.
        about (str): A brief description about the user.
        metadata (dict, optional): Additional metadata about the user. Defaults to an empty dict.
        client (CozoClient, optional): The CozoDB client instance to run the query. Defaults to a pre-configured client instance.

    Returns:
        pd.DataFrame: A DataFrame containing the result of the query execution.
    """

    user_id = user_id or uuid4()
    data.metadata = data.metadata or {}
    user_data = data.model_dump()

    create_query = """
        # Then create the user
        ?[user_id, developer_id, name, about, metadata] <- [
            [to_uuid($user_id), to_uuid($developer_id), $name, $about, $metadata]
        ]

        :insert users {
            developer_id,
            user_id =>
            name,
            about,
            metadata,
        }
        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        create_query,
    ]

    return (
        queries,
        {
            "user_id": str(user_id),
            "developer_id": str(developer_id),
            **user_data,
        },
    )

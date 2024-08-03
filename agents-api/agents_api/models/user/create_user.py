"""
This module contains the functionality for creating a new user in the CozoDB database.
It defines a query for inserting user data into the 'users' relation.
"""

from uuid import UUID, uuid4

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import CreateUserRequest, User
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    wrap_in_class,
)


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(User, one=True, transform=lambda d: {"id": UUID(d.pop("user_id")), **d})
@cozo_query
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

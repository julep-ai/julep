"""
This module contains the implementation of the delete_user_query function, which is responsible for deleting an user and its related default settings from the CozoDB database.
"""

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
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": UUID(d.pop("file_id")),
        "deleted_at": utcnow(),
        "jobs": [],
    },
    _kind="deleted",
)
@cozo_query
@beartype
def delete_file(*, developer_id: UUID, file_id: UUID) -> tuple[list[str], dict]:
    """
    Constructs and returns a datalog query for deleting an file from the database.

    Parameters:
        developer_id (UUID): The UUID of the developer owning the file.
        file_id (UUID): The UUID of the file to be deleted.
        client (CozoClient, optional): An instance of the CozoClient to execute the query.

    Returns:
        ResourceDeletedResponse: The response indicating the deletion of the user.
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "files", file_id=file_id),
        """
        ?[file_id, developer_id] <- [[$file_id, $developer_id]]

        :delete files {
            developer_id,
            file_id
        }
        :returning
        """,
    ]

    return (queries, {"file_id": str(file_id), "developer_id": str(developer_id)})

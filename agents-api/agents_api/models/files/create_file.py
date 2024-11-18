"""
This module contains the functionality for creating a new user in the CozoDB database.
It defines a query for inserting user data into the 'users' relation.
"""

import base64
import hashlib
from typing import Any, TypeVar
from uuid import UUID, uuid4

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import CreateFileRequest, File
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
    File,
    one=True,
    transform=lambda d: {
        **d,
        "id": d["file_id"],
        "content": "DUMMY: NEED TO FETCH CONTENT FROM BLOB STORAGE",
    },
    _kind="inserted",
)
@cozo_query
@increase_counter("create_file")
@beartype
def create_file(
    *,
    developer_id: UUID,
    file_id: UUID | None = None,
    data: CreateFileRequest,
) -> tuple[list[str], dict]:
    """
    Constructs and executes a datalog query to create a new file in the CozoDB database.

    Parameters:
        user_id (UUID): The unique identifier for the user.
        developer_id (UUID): The unique identifier for the developer creating the file.
    """

    file_id = file_id or uuid4()
    file_data = data.model_dump(exclude={"content"})

    content_bytes = base64.b64decode(data.content)
    size = len(content_bytes)
    hash = hashlib.sha256(content_bytes).hexdigest()

    create_query = """
        # Then create the file
        ?[file_id, developer_id, name, description, mime_type, size, hash] <- [
            [to_uuid($file_id), to_uuid($developer_id), $name, $description, $mime_type, $size, $hash]
        ]

        :insert files {
            developer_id,
            file_id =>
            name,
            description,
            mime_type,
            size,
            hash,
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
            "file_id": str(file_id),
            "developer_id": str(developer_id),
            "size": size,
            "hash": hash,
            **file_data,
        },
    )

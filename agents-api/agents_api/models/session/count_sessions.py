"""This module contains functions for querying session data from the 'cozodb' database."""

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

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
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(dict, one=True)
@cozo_query
@beartype
def count_sessions(
    *,
    developer_id: UUID,
) -> tuple[list[str], dict]:
    """
    Counts sessions from the 'cozodb' database.

    Parameters:
        developer_id (UUID): The developer's ID to filter sessions by.
    """

    count_query = """
        input[developer_id] <- [[
            to_uuid($developer_id),
        ]]

        counter[count(id)] :=
            input[developer_id],
            *sessions{
                developer_id,
                session_id: id,
            }

        ?[count] := counter[count]
    """

    queries = [
        verify_developer_id_query(developer_id),
        count_query,
    ]

    return (queries, {"developer_id": str(developer_id)})

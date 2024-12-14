"""Module for retrieving document snippets from the CozoDB based on document IDs."""

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...common.protocol.developers import Developer
from ..utils import (
    cozo_query,
    partialclass,
    pg_query,
    rewrap_exceptions,
    verify_developer_id_query,
    wrap_in_class,
)

ModelT = TypeVar("ModelT", bound=Any)
T = TypeVar("T")


@rewrap_exceptions({QueryException: partialclass(HTTPException, status_code=401)})
@cozo_query
@beartype
def verify_developer(
    *,
    developer_id: UUID,
) -> tuple[str, dict]:
    return (verify_developer_id_query(developer_id), {})


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=403),
        ValidationError: partialclass(HTTPException, status_code=500),
    }
)
@wrap_in_class(Developer, one=True, transform=lambda d: {**d, "id": d["developer_id"]})
@pg_query
@beartype
async def get_developer(
    *,
    developer_id: UUID,
) -> tuple[str, list]:
    developer_id = str(developer_id)
    query = "SELECT * FROM developers WHERE developer_id = $1"

    return (
        query,
        [developer_id],
    )

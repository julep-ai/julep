from typing import Any, Literal, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import User
from ...common.utils import json
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
@wrap_in_class(User)
@cozo_query
@beartype
def list_users(
    *,
    developer_id: UUID,
    limit: int = 100,
    offset: int = 0,
    sort_by: Literal["created_at", "updated_at"] = "created_at",
    direction: Literal["asc", "desc"] = "desc",
    metadata_filter: dict[str, Any] = {},
) -> tuple[list[str], dict]:
    """
    Queries the 'cozodb' database to list users associated with a specific developer.

    Parameters:
    - developer_id (UUID): The unique identifier of the developer.
    - limit (int): The maximum number of users to return. Defaults to 100.
    - offset (int): The number of users to skip before starting to collect the result set. Defaults to 0.
    - metadata_filter (dict[str, Any]): A dictionary representing filters to apply on user metadata.

    Returns:
    - pd.DataFrame: A DataFrame containing the queried user data.
    """
    # Construct a filter string for the metadata based on the provided dictionary.
    metadata_filter_str = ", ".join(
        [
            f"metadata->{json.dumps(k)} == {json.dumps(v)}"
            for k, v in metadata_filter.items()
        ]
    )

    sort = f"{'-' if direction == 'desc' else ''}{sort_by}"

    # Define the datalog query for retrieving user information based on the specified filters and sorting them by creation date in descending order.
    list_query = f"""
    input[developer_id] <- [[to_uuid($developer_id)]]

    ?[
        id,
        name,
        about,
        created_at,
        updated_at,
        metadata,
    ] :=
        input[developer_id],
        *users {{
            user_id: id,
            developer_id,
            name,
            about,
            created_at,
            updated_at,
            metadata,
        }},
        {metadata_filter_str}

    :limit $limit
    :offset $offset
    :sort {sort}
    """

    queries = [
        verify_developer_id_query(developer_id),
        list_query,
    ]

    # Execute the datalog query with the specified parameters and return the results as a DataFrame.
    return (
        queries,
        {"developer_id": str(developer_id), "limit": limit, "offset": offset},
    )

from typing import Any, TypeVar
from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import ResourceUpdatedResponse, UpdateUserRequest
from ...common.utils.cozo import cozo_process_mutate_data
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
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    ResourceUpdatedResponse,
    one=True,
    transform=lambda d: {"id": d["user_id"], "jobs": [], **d},
    _kind="inserted",
)
@cozo_query
@beartype
def update_user(
    *, developer_id: UUID, user_id: UUID, data: UpdateUserRequest
) -> tuple[list[str], dict]:
    """Updates user information in the 'cozodb' database.

    Parameters:
        developer_id (UUID): The developer's unique identifier.
        user_id (UUID): The user's unique identifier.
        client (CozoClient): The Cozo database client instance.
        **update_data: Arbitrary keyword arguments representing the data to update.

    Returns:
        pd.DataFrame: A DataFrame containing the result of the update operation.
    """
    user_id = str(user_id)
    developer_id = str(developer_id)
    update_data = data.model_dump()

    # Prepares the update data by filtering out None values and adding user_id and developer_id.
    user_update_cols, user_update_vals = cozo_process_mutate_data(
        {
            **{k: v for k, v in update_data.items() if v is not None},
            "user_id": user_id,
            "developer_id": developer_id,
        }
    )

    # Constructs the update operation for the user, setting new values and updating 'updated_at'.
    update_query = f"""
        # update the user
        # This line updates the user's information based on the provided columns and values.
        input[{user_update_cols}] <- $user_update_vals
        original[created_at] := *users{{
            developer_id: to_uuid($developer_id),
            user_id: to_uuid($user_id),
            created_at,
        }},

        ?[created_at, updated_at, {user_update_cols}] :=
            input[{user_update_cols}],
            original[created_at],
            updated_at = now(),

        :put users {{
            created_at,
            updated_at,
            {user_update_cols}
        }}
        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "users", user_id=user_id),
        update_query,
    ]

    return (
        queries,
        {
            "user_update_vals": user_update_vals,
            "developer_id": developer_id,
            "user_id": user_id,
        },
    )

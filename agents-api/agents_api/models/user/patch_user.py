"""Module for generating datalog queries to update user information in the 'cozodb' database."""

from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import PatchUserRequest, ResourceUpdatedResponse
from ...common.utils.cozo import cozo_process_mutate_data
from ...common.utils.datetime import utcnow
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
    verify_developer_owns_resource_query,
    wrap_in_class,
)


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
    _kind="replaced",
)
@cozo_query
@beartype
def patch_user(
    *,
    developer_id: UUID,
    user_id: UUID,
    data: PatchUserRequest,
) -> tuple[list[str], dict]:
    """
    Generates a datalog query for updating a user's information.

    Parameters:
    - developer_id (UUID): The UUID of the developer.
    - user_id (UUID): The UUID of the user to be updated.
    - **update_data: Arbitrary keyword arguments representing the data to be updated.

    Returns:
    - tuple[str, dict]: A pandas DataFrame containing the results of the query execution.
    """

    update_data = data.model_dump(exclude_unset=True)

    # Prepare data for mutation by filtering out None values and adding system-generated fields.
    metadata = update_data.pop("metadata", {}) or {}
    user_update_cols, user_update_vals = cozo_process_mutate_data(
        {
            **{k: v for k, v in update_data.items() if v is not None},
            "user_id": str(user_id),
            "developer_id": str(developer_id),
            "updated_at": utcnow().timestamp(),
        }
    )

    # Construct the datalog query for updating user information.
    update_query = f"""
        # update the user
        input[{user_update_cols}] <- $user_update_vals
        
        ?[{user_update_cols}, metadata] := 
            input[{user_update_cols}],
            *users {{
                user_id: to_uuid($user_id),
                metadata: md,
            }},
            metadata = concat(md, $metadata)

        :update users {{
            {user_update_cols}, metadata
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
            "metadata": metadata,
            "user_id": str(user_id),
        },
    )

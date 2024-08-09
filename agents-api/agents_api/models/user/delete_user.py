"""
This module contains the implementation of the delete_user_query function, which is responsible for deleting an user and its related default settings from the CozoDB database.
"""

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


@rewrap_exceptions(
    {
        QueryException: partialclass(HTTPException, status_code=400),
        ValidationError: partialclass(HTTPException, status_code=400),
        TypeError: partialclass(HTTPException, status_code=400),
    }
)
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": UUID(d.pop("user_id")),
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@cozo_query
@beartype
def delete_user(*, developer_id: UUID, user_id: UUID) -> tuple[list[str], dict]:
    """
    Constructs and returns a datalog query for deleting an user and its default settings from the database.

    Parameters:
    - developer_id (UUID): The UUID of the developer owning the user.
    - user_id (UUID): The UUID of the user to be deleted.
    - client (CozoClient, optional): An instance of the CozoClient to execute the query.

    Returns:
    - ResourceDeletedResponse: The response indicating the deletion of the user.
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(developer_id, "users", user_id=user_id),
        """
        # Delete docs
        ?[user_id, doc_id] :=
            *docs{
                owner_id: user_id,
                owner_type: "user",
                doc_id,
            }, user_id = to_uuid($user_id)

        :delete docs {
            user_id,
            doc_id
        }
        :returning
        """,
        """
        # Delete the user
        ?[user_id, developer_id] <- [[$user_id, $developer_id]]

        :delete users {
            developer_id,
            user_id
        }
        :returning
        """,
    ]

    return (queries, {"user_id": str(user_id), "developer_id": str(developer_id)})

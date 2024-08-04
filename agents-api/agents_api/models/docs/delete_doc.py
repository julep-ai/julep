from typing import Literal
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
        "id": UUID(d.pop("doc_id")),
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@cozo_query
@beartype
def delete_doc(
    *,
    developer_id: UUID,
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
    doc_id: UUID,
) -> tuple[list[str], dict]:
    """Constructs and returns a datalog query for deleting documents and associated information snippets.

    This function targets the 'cozodb' database, allowing for the removal of documents and their related information snippets based on the provided document ID and owner (user or agent).

    Parameters:
        owner_type (Literal["user", "agent"]): The type of the owner, either 'user' or 'agent'.
        owner_id (UUID): The UUID of the owner.
        doc_id (UUID): The UUID of the document to be deleted.
        client (CozoClient): An instance of the CozoClient to execute the query.

    Returns:
        pd.DataFrame: The result of the executed datalog query.
    """
    # Convert UUID parameters to string format for use in the datalog query
    owner_id = str(owner_id)
    doc_id = str(doc_id)

    # The following query is divided into two main parts:
    # 1. Deleting information snippets associated with the document
    # 2. Deleting the document itself from the owner's collection
    delete_snippets_query = """
        # This section constructs the subquery for identifying and deleting all information snippets associated with the given document ID.
        # Delete snippets
        input[doc_id] <- [[to_uuid($doc_id)]]
        ?[doc_id, index] :=
            input[doc_id],
            *snippets {
                doc_id,
                index,
            }

        :delete snippets {
            doc_id,
            index
        }
    """

    delete_doc_query = """
        # This section constructs the subquery for deleting the document from the specified owner's (user or agent) document collection.
        # Delete the docs
        ?[doc_id, owner_id, owner_type] <- [[
            to_uuid($doc_id),
            to_uuid($owner_id),
            $owner_type,
        ]]

        :delete docs {
            doc_id,
            owner_type,
            owner_id,
        }
        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        verify_developer_owns_resource_query(
            developer_id, f"{owner_type}s", **{f"{owner_type}_id": owner_id}
        ),
        delete_snippets_query,
        delete_doc_query,
    ]

    return (queries, {"doc_id": doc_id, "owner_id": owner_id, "owner_type": owner_type})

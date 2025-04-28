from typing import Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Delete doc query
delete_doc_query = """
DELETE FROM docs
WHERE developer_id = $1
  AND doc_id = $2
RETURNING doc_id;
"""

delete_doc_owners_query = """
DELETE FROM doc_owners
WHERE developer_id = $1
    AND doc_id = $2
    AND owner_type = $3
    AND owner_id = $4
RETURNING doc_id;
"""


@rewrap_exceptions(common_db_exceptions("doc", ["delete"]))
@wrap_in_class(
    ResourceDeletedResponse,
    one=True,
    transform=lambda d: {
        "id": d["doc_id"],
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@pg_query
@beartype
async def delete_doc(
    *,
    developer_id: UUID,
    doc_id: UUID,
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
) -> list[tuple[str, list]]:
    """
    Deletes a doc (and associated doc_owners) for the given developer and doc_id.
    If owner_type/owner_id is specified, only remove doc if that matches.

    Parameters:
        developer_id (UUID): The ID of the developer.
        doc_id (UUID): The ID of the document.
        owner_type (Literal["user", "agent"]): The type of the owner of the documents.
        owner_id (UUID): The ID of the owner of the documents.

    Returns:
        tuple[str, list]: SQL query and parameters for deleting the document.
    """
    return [
        (delete_doc_query, [developer_id, doc_id]),
        (delete_doc_owners_query, [developer_id, doc_id, owner_type, owner_id]),
    ]

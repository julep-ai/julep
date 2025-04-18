from typing import Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import BulkDeleteDocsRequest, ResourceDeletedResponse
from ...common.utils.datetime import utcnow
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import (
    build_metadata_filter_conditions,
    pg_query,
    rewrap_exceptions,
    wrap_in_class,
)


@rewrap_exceptions(common_db_exceptions("doc", ["delete"]))
@wrap_in_class(
    ResourceDeletedResponse,
    transform=lambda d: {
        "id": d["doc_id"],
        "deleted_at": utcnow(),
        "jobs": [],
    },
)
@pg_query
@beartype
async def bulk_delete_docs(
    *,
    developer_id: UUID,
    owner_id: UUID,
    owner_type: Literal["user", "agent"],
    data: BulkDeleteDocsRequest,
) -> tuple[str, list]:
    """
    Deletes docs and their associated doc_owners entries for the given criteria.
    """
    metadata_filter = data.metadata_filter or {}
    delete_all = getattr(data, "delete_all", False)

    if not delete_all and not metadata_filter:
        query = """
        SELECT doc_id FROM docs WHERE 1=0;
        """
        return query, []

    # Initialize base parameters
    params = [developer_id, owner_type, owner_id]

    # Use the utility function to safely build metadata filter conditions with table alias
    metadata_conditions, params = build_metadata_filter_conditions(
        params, metadata_filter if not delete_all else {}, table_alias="d."
    )

    query = f"""
    WITH deleted_docs AS (
        DELETE FROM docs d
        WHERE d.developer_id = $1
            AND EXISTS (
                SELECT 1
                FROM doc_owners o
                WHERE o.doc_id = d.doc_id
                AND o.developer_id = d.developer_id
                AND o.owner_type = $2
                AND o.owner_id = $3
                {metadata_conditions}
            )
        RETURNING d.doc_id
    ),
    deleted_owners AS (
        DELETE FROM doc_owners
        WHERE developer_id = $1
        AND owner_type = $2
        AND owner_id = $3
        AND doc_id IN (SELECT doc_id FROM deleted_docs)
    )
    SELECT doc_id FROM deleted_docs;
    """

    return query, params

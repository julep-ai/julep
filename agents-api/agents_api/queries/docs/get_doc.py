from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Doc
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class
from .utils import transform_doc

# get doc with embedding
doc_with_embedding_query = """
SELECT
    d.doc_id,
    d.developer_id,
    d.title,
    array_agg(d.content ORDER BY d.index) as content,
    array_agg(d.index ORDER BY d.index) as indices,
    array_agg(e.embedding ORDER BY d.index) as embeddings,
    d.modality,
    d.embedding_model,
    d.embedding_dimensions,
    d.language,
    d.metadata,
    d.created_at
FROM docs d
LEFT JOIN docs_embeddings e
    ON d.doc_id = e.doc_id
    AND e.embedding IS NOT NULL
WHERE d.developer_id = $1
    AND d.doc_id = $2
GROUP BY
    d.doc_id,
    d.developer_id,
    d.title,
    d.modality,
    d.embedding_model,
    d.embedding_dimensions,
    d.language,
    d.metadata,
    d.created_at
ORDER BY d.created_at DESC
LIMIT 1;
"""

# get doc without embedding
doc_without_embedding_query = """
SELECT
    d.doc_id,
    d.developer_id,
    d.title,
    array_agg(d.content ORDER BY d.index) as content,
    array_agg(d.index ORDER BY d.index) as indices,
    d.modality,
    d.embedding_model,
    d.embedding_dimensions,
    d.language,
    d.metadata,
    d.created_at
FROM docs d
WHERE d.developer_id = $1
    AND d.doc_id = $2
GROUP BY
    d.doc_id,
    d.developer_id,
    d.title,
    d.modality,
    d.embedding_model,
    d.embedding_dimensions,
    d.language,
    d.metadata,
    d.created_at
ORDER BY d.created_at DESC
LIMIT 1;
"""

@rewrap_exceptions(common_db_exceptions("doc", ["get"]))
@wrap_in_class(
    Doc,
    one=True,
    transform=transform_doc,
)
@pg_query
@beartype
async def get_doc(
    *,
    developer_id: UUID,
    doc_id: UUID,
) -> tuple[str, list]:
    """
    Fetch a single doc with its embedding, grouping all content chunks and embeddings.

    Parameters:
        developer_id (UUID): The ID of the developer.
        doc_id (UUID): The ID of the document.

    Returns:
        tuple[str, list]: SQL query and parameters for fetching the document.
    """
    return (
        doc_with_embedding_query,
        [developer_id, doc_id],
    )

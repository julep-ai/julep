import json
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Doc
from ...common.utils.db_exceptions import common_db_exceptions
from ..utils import pg_query, rewrap_exceptions, wrap_in_class

# Update the query to use DISTINCT ON to prevent duplicates
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


def transform_get_doc(d: dict) -> dict:
    content = d["content"][0] if len(d["content"]) == 1 else d["content"]

    embeddings = d["embeddings"][0] if len(d["embeddings"]) == 1 else d["embeddings"]

    if isinstance(embeddings, str):
        embeddings = json.loads(embeddings)
    elif isinstance(embeddings, list) and all(isinstance(e, str) for e in embeddings):
        embeddings = [json.loads(e) for e in embeddings]

    if embeddings and all((e is None) for e in embeddings):
        embeddings = None

    return {
        **d,
        "id": d["doc_id"],
        "content": content,
        "embeddings": embeddings,
    }


@rewrap_exceptions(common_db_exceptions("doc", ["get"]))
@wrap_in_class(
    Doc,
    one=True,
    transform=transform_get_doc,
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

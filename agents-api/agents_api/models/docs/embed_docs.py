"""Module for embedding documents in the cozodb database. Contains functions to update document embeddings."""

from uuid import UUID


from ..utils import cozo_query


@cozo_query
def embed_docs_snippets_query(
    doc_id: UUID,
    snippet_indices: list[int],
    embeddings: list[list[float]],
) -> tuple[str, dict]:
    """Embeds document snippets in the cozodb database.

    Parameters:
    doc_id (UUID): The unique identifier for the document.
    snippet_indices (list[int]): Indices of the snippets in the document.
    embeddings (list[list[float]]): Embedding vectors for the snippets.

    Returns:
    tuple[str, dict]: A DataFrame containing the results of the embedding operation.
    """

    doc_id = str(doc_id)
    # Ensure the number of snippet indices matches the number of embeddings.
    assert len(snippet_indices) == len(embeddings)

    # Prepare records for the database query by combining doc_id, snippet indices, and embeddings.
    records = [
        [doc_id, snippet_idx, embedding]
        for snippet_idx, embedding in zip(snippet_indices, embeddings)
    ]

    # Define the datalog query for updating document snippet embeddings in the database.
    query = """
    {
        ?[doc_id, snippet_idx, embedding] <- $records

        :update information_snippets {
            doc_id,
            snippet_idx,
            embedding,
        }
        :returning
    }"""

    return (query, {"records": records})

"""Module for embedding documents in the cozodb database. Contains functions to update document embeddings."""

from uuid import UUID

from beartype import beartype
from fastapi import HTTPException
from pycozo.client import QueryException
from pydantic import ValidationError

from ...autogen.openapi_model import ResourceUpdatedResponse
from ...common.utils.cozo import cozo_process_mutate_data
from ...common.utils.datetime import utcnow
from ..utils import (
    cozo_query,
    partialclass,
    rewrap_exceptions,
    verify_developer_id_query,
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
    transform=lambda d: {"id": d["doc_id"], "updated_at": utcnow(), "jobs": []},
)
@cozo_query
@beartype
def embed_snippets(
    *,
    developer_id: UUID,
    doc_id: UUID,
    snippet_indices: list[int] | tuple[int],
    embeddings: list[list[float]],
    embedding_size: int = 1024,
) -> tuple[list[str], dict]:
    """Embeds document snippets in the cozodb database.

    Parameters:
    doc_id (UUID): The unique identifier for the document.
    snippet_indices (list[int]): Indices of the snippets in the document.
    embeddings (list[list[float]]): Embedding vectors for the snippets.
    """

    doc_id = str(doc_id)

    # Ensure the number of snippet indices matches the number of embeddings.
    assert len(snippet_indices) == len(embeddings)
    assert all(len(embedding) == embedding_size for embedding in embeddings)
    assert min(snippet_indices) >= 0

    # Ensure all embeddings are non-zero.
    assert all(sum(embedding) for embedding in embeddings)

    # Create a list of records to update the document snippet embeddings in the database.
    records = [
        {"doc_id": doc_id, "index": snippet_idx, "embedding": embedding}
        for snippet_idx, embedding in zip(snippet_indices, embeddings)
    ]

    cols, vals = cozo_process_mutate_data(records)

    # Ensure that index is present in the records.
    check_indices_query = f"""
        ?[index] :=
            *snippets {{
                doc_id: $doc_id,
                index,
            }},
            index > {max(snippet_indices)}

        :assert none
    """

    # Define the datalog query for updating document snippet embeddings in the database.
    embed_query = f"""
        ?[{cols}] <- $vals

        :update snippets {{ {cols} }}
        :returning
    """

    queries = [
        verify_developer_id_query(developer_id),
        check_indices_query,
        embed_query,
    ]

    return (queries, {"vals": vals, "doc_id": doc_id})

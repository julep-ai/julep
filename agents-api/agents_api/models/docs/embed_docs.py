"""Module for embedding documents in the cozodb database. Contains functions to update document embeddings."""

from uuid import UUID

import pandas as pd
from pycozo.client import Client as CozoClient

from ...clients.cozo import client


"""Embeds document snippets in the cozodb database.

Parameters:
doc_id (UUID): The unique identifier for the document.
snippet_indices (list[int]): Indices of the snippets in the document.
embeddings (list[list[float]]): Embedding vectors for the snippets.
client (CozoClient, optional): The Cozo client to interact with the database. Defaults to a pre-configured client instance.

Returns:
pd.DataFrame: A DataFrame containing the results of the embedding operation.
"""


def embed_docs_snippets_query(
    doc_id: UUID,
    snippet_indices: list[int],
    embeddings: list[list[float]],
    client: CozoClient = client,
) -> pd.DataFrame:
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

    return client.run(query, {"records": records})

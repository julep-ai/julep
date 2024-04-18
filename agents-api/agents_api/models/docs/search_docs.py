"""This module contains functions for searching documents in the CozoDB based on embedding queries."""

from typing import Literal
from uuid import UUID


from ..utils import cozo_query


@cozo_query
def search_docs_snippets_by_embedding_query(
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
    query_embedding: list[float],
    k: int = 3,
    confidence: float = 0.8,
) -> tuple[str, dict]:
    """
    Searches for document snippets in CozoDB by embedding query.

    Parameters:
    - owner_type (Literal["user", "agent"]): The type of the owner of the documents.
    - owner_id (UUID): The unique identifier of the owner.
    - query_embedding (list[float]): The embedding vector of the query.
    - k (int, optional): The number of nearest neighbors to retrieve. Defaults to 3.
    - confidence (float, optional): The confidence threshold for filtering results. Defaults to 0.8.

    Returns:
    - pd.DataFrame: A DataFrame containing the search results.
    """

    owner_id = str(owner_id)
    # Calculate the search radius based on confidence level
    radius: float = 1.0 - confidence

    # Construct the datalog query for searching document snippets
    query = f"""
    {{
        input[
            {owner_type}_id,
            query_embedding,
        ] <- [[
            to_uuid($owner_id),
            vec($query_embedding),
        ]]

        candidate[
            doc_id
        ] := input[{owner_type}_id, _],
            *{owner_type}_docs {{
                {owner_type}_id,
                doc_id
            }}

        ?[
            {owner_type}_id,
            doc_id,
            title,
            snippet,
            snippet_idx,
            distance,
            vector,
        ] := input[{owner_type}_id, query_embedding],
            candidate[doc_id],
            ~information_snippets:embedding_space {{
                doc_id,
                snippet_idx,
                title,
                snippet |
                query: query_embedding,
                k: $k,
                ef: 128,
                radius: $radius,
                bind_distance: distance,
                bind_vector: vector,
            }}

        # Sort the results by distance to find the closest matches
        :sort distance
    }}"""

    return (
        query,
        {
            "owner_id": owner_id,
            "query_embedding": query_embedding,
            "k": k,
            "radius": radius,
        },
    )

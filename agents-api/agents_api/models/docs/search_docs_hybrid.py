"""This module contains functions for searching documents in the CozoDB based on embedding queries."""

from statistics import mean, stdev
from typing import Any, Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import DocReference
from .search_docs_by_embedding import search_docs_by_embedding
from .search_docs_by_text import search_docs_by_text


# Distribution based score normalization
# https://medium.com/plain-simple-software/distribution-based-score-fusion-dbsf-a-new-approach-to-vector-search-ranking-f87c37488b18
def dbsf_normalize(scores: list[float]) -> list[float]:
    """
    Scores scaled using minmax scaler with our custom feature range
    (extremes indicated as 3 standard deviations from the mean)
    """
    if len(scores) < 2:
        return scores

    sd = stdev(scores)
    if sd == 0:
        return scores

    m = mean(scores)
    m3d = 3 * sd + m
    m_3d = m - 3 * sd

    return [(s - m_3d) / (m3d - m_3d) for s in scores]


def dbsf_fuse(
    text_results: list[DocReference],
    embedding_results: list[DocReference],
    alpha: float = 0.7,  # Weight of the embedding search results (this is a good default)
) -> list[DocReference]:
    """
    Weighted reciprocal-rank fusion of text and embedding search results
    """
    all_docs = {doc.id: doc for doc in text_results + embedding_results}

    text_scores: dict[UUID, float] = {
        doc.id: -(doc.distance or 0.0) for doc in text_results
    }

    # Because these are cosine distances, we need to invert them
    embedding_scores: dict[UUID, float] = {
        doc.id: 1.0 - doc.distance for doc in embedding_results
    }

    # normalize the scores
    text_scores_normalized = dbsf_normalize(list(text_scores.values()))
    text_scores = {
        doc_id: score
        for doc_id, score in zip(text_scores.keys(), text_scores_normalized)
    }

    embedding_scores_normalized = dbsf_normalize(list(embedding_scores.values()))
    embedding_scores = {
        doc_id: score
        for doc_id, score in zip(embedding_scores.keys(), embedding_scores_normalized)
    }

    # Combine the scores
    text_weight: float = 1 - alpha
    embedding_weight: float = alpha

    combined_scores = []

    for id in all_docs.keys():
        text_score = text_weight * text_scores.get(id, 0)
        embedding_score = embedding_weight * embedding_scores.get(id, 0)

        combined_scores.append((id, text_score + embedding_score))

    # Sort by the combined score
    combined_scores = sorted(combined_scores, key=lambda x: x[1], reverse=True)

    # Rank the results
    ranked_results = []
    for id, score in combined_scores:
        doc = all_docs[id].model_copy()
        doc.distance = 1.0 - score
        ranked_results.append(doc)

    return ranked_results


@beartype
def search_docs_hybrid(
    *,
    developer_id: UUID,
    owners: list[tuple[Literal["user", "agent"], UUID]],
    query: str,
    query_embedding: list[float],
    k: int = 3,
    alpha: float = 0.7,  # Weight of the embedding search results (this is a good default)
    embed_search_options: dict = {},
    text_search_options: dict = {},
    metadata_filter: dict[str, Any] = {},
) -> list[DocReference]:
    # TODO: We should probably parallelize these queries
    text_results = search_docs_by_text(
        developer_id=developer_id,
        owners=owners,
        query=query,
        k=2 * k,
        metadata_filter=metadata_filter,
        **text_search_options,
    )

    embedding_results = search_docs_by_embedding(
        developer_id=developer_id,
        owners=owners,
        query_embedding=query_embedding,
        k=2 * k,
        metadata_filter=metadata_filter,
        **embed_search_options,
    )

    return dbsf_fuse(text_results, embedding_results, alpha)[:k]

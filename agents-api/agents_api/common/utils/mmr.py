from __future__ import annotations

import logging
from typing import TypeVar

import numpy as np
from beartype import beartype

from ...autogen.openapi_model import DocReference

Matrix = list[list[float]] | list[np.ndarray] | np.ndarray

logger = logging.getLogger(__name__)

MIN_DOCS_WITH_EMBEDDINGS = 2

T = TypeVar("T")


def _cosine_similarity(x: Matrix, y: Matrix) -> np.ndarray:
    """Row-wise cosine similarity between two equal-width matrices.

    Args:
        x: A matrix of shape (n, m).
        y: A matrix of shape (k, m).

    Returns:
        A matrix of shape (n, k) where each element (i, j) is the cosine similarity
        between the ith row of X and the jth row of Y.

    Raises:
        ValueError: If the number of columns in X and Y are not the same.
        ImportError: If numpy is not installed.
    """

    if len(x) == 0 or len(y) == 0:
        return np.array([])

    x = [xx for xx in x if xx is not None]
    y = [yy for yy in y if yy is not None]

    x = np.array(x)
    y = np.array(y)
    if x.shape[1] != y.shape[1]:
        msg = f"Number of columns in X and Y must be the same. X has shape {x.shape} and Y has shape {y.shape}."
        raise ValueError(msg)
    try:
        import simsimd as simd  # type: ignore

        x = np.array(x, dtype=np.float32)
        y = np.array(y, dtype=np.float32)
        return 1 - np.array(simd.cdist(x, y, metric="cosine"))
    except ImportError:
        logger.debug(
            "Unable to import simsimd, defaulting to NumPy implementation. If you want "
            "to use simsimd please install with `pip install simsimd`.",
        )
        x_norm = np.linalg.norm(x, axis=1)
        y_norm = np.linalg.norm(y, axis=1)
        # Ignore divide by zero errors run time warnings as those are handled below.
        with np.errstate(divide="ignore", invalid="ignore"):
            similarity = np.dot(x, y.T) / np.outer(x_norm, y_norm)
        similarity[np.isnan(similarity) | np.isinf(similarity)] = 0.0
        return similarity


@beartype
def maximal_marginal_relevance(
    query_embedding: np.ndarray,
    embedding_list: list,
    lambda_mult: float = 0.5,
    k: int = 4,
) -> list[int]:
    """Calculate maximal marginal relevance.

    Args:
        query_embedding: The query embedding.
        embedding_list: A list of embeddings.
        lambda_mult: The lambda parameter for MMR. Default is 0.5.
        k: The number of embeddings to return. Default is 4.

    Returns:
        A list of indices of the embeddings to return.

    Raises:
        ImportError: If numpy is not installed.
    """

    if min(k, len(embedding_list)) <= 0:
        return []
    if query_embedding.ndim == 1:
        query_embedding = np.expand_dims(query_embedding, axis=0)
    similarity_to_query = _cosine_similarity(query_embedding, embedding_list)[0]
    most_similar = int(np.argmax(similarity_to_query))
    idxs = [most_similar]
    selected = np.array([embedding_list[most_similar]])
    while len(idxs) < min(k, len(embedding_list)):
        best_score = -np.inf
        idx_to_add = -1
        similarity_to_selected = _cosine_similarity(embedding_list, selected)
        for i, query_score in enumerate(similarity_to_query):
            if i in idxs:
                continue
            redundant_score = max(similarity_to_selected[i])
            equation_score = lambda_mult * query_score - (1 - lambda_mult) * redundant_score
            if equation_score > best_score:
                best_score = equation_score
                idx_to_add = i
        idxs.append(idx_to_add)
        selected = np.append(selected, [embedding_list[idx_to_add]], axis=0)
    return idxs


@beartype
def apply_mmr_to_docs(
    docs: list[DocReference], query_embedding: np.ndarray, limit: int, mmr_strength: float
) -> list[DocReference]:
    """
    Apply Maximal Marginal Relevance to a list of document references.

    Parameters:
        docs: List of document references
        query_embedding: The embedding vector of the query
        limit: Maximum number of documents to return
        mmr_strength: Strength of MMR (0-1), where 0 means no diversity and 1 means maximum diversity

    Returns:
        List of document references after applying MMR
    """
    # Filter docs with embeddings and extract embeddings in one pass
    docs_with_embeddings = []
    embeddings = []
    for doc in docs:
        if doc.snippet.embedding is not None:
            docs_with_embeddings.append(doc)
            embeddings.append(doc.snippet.embedding)

    if len(docs_with_embeddings) >= MIN_DOCS_WITH_EMBEDDINGS:
        # Apply MMR
        indices = maximal_marginal_relevance(
            query_embedding,
            embeddings,
            k=min(limit, len(docs_with_embeddings)),
            lambda_mult=1 - mmr_strength,
        )
        # Deduplicate indices while preserving their order
        unique_indices: list[int] = []
        seen: set[int] = set()
        for idx in indices:
            if idx not in seen:
                seen.add(idx)
                unique_indices.append(idx)

        return [docs_with_embeddings[i] for i in unique_indices]

    # If docs are present but no embeddings are present for any of the docs, return the top k docs
    return docs[:limit]

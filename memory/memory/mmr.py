from typing import Callable, Iterable, TypeVar

import numpy as np
from numpy.linalg import norm
from sklearn.metrics import pairwise

T = TypeVar("T")

# http://www.cs.cmu.edu/~jgc/publication/The_Use_MMR_Diversity_Based_LTMIR_1998.pdf
# MMR = argmax(L*sim(Di, Q) - (1-L)*sim(Di, Dj))


def cosine_similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))


def argmax(ls: list[T], max_by: Callable[[T], float]) -> T:
    return max(ls, key=max_by)


def mmr(
    docs: list[T],
    query_embedding: list[float] | np.ndarray,
    get_embedding: Callable[[T], list[float]] = lambda x: x,
    lambda_mult: float = 0.5,
) -> Iterable[T]:
    docs_len = len(docs)

    # Return as is if docs is an empty list
    if not docs_len:
        yield from docs
        return

    query_embedding: np.ndarray = np.array(query_embedding)

    # Get doc embeddings
    doc_embeddings: list[list[float]] = list(map(get_embedding, docs))
    doc_embeddings: np.ndarray = np.array(doc_embeddings)

    similarity_matrix = pairwise.cosine_similarity(doc_embeddings)

    # Container to track yielded indices
    yielded: list[int] = []

    # Iterate until all yielded
    while docs_len != len(yielded):
        # Get doc1 and remaining indices
        remaining = [j for j in range(docs_len) if j not in yielded]
        i, *rest = remaining

        # Continue if done (this will exit the loop)
        if not rest:
            # Yield last doc and add it to yielded
            yield docs[i]
            yielded.append(i)

            continue

        # Calculate similarity between query and doc1
        doc_i_q_similarity = cosine_similarity(query_embedding, doc_embeddings[i])

        # Calculate l1 (lambda * similarity(doc1, q)
        l1 = lambda_mult * doc_i_q_similarity

        # Given any j, calculate mmr score using the algorithm
        def mmr_score(j: int):
            l2 = (1 - lambda_mult) * similarity_matrix[i][j]
            return l1 - l2

        # Get the index for the highest scoring doc
        best_j = argmax(rest, max_by=mmr_score)

        # Yield and continue
        yield docs[best_j]
        yielded.append(best_j)

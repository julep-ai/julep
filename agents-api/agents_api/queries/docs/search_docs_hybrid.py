from typing import List, Literal
from uuid import UUID

from beartype import beartype

from ...autogen.openapi_model import Doc
from .search_docs_by_embedding import search_docs_by_embedding
from .search_docs_by_text import search_docs_by_text


def dbsf_normalize(scores: List[float]) -> List[float]:
    """
    Example distribution-based normalization: clamp each score
    from (mean - 3*stddev) to (mean + 3*stddev) and scale to 0..1
    """
    import statistics

    if len(scores) < 2:
        return scores
    m = statistics.mean(scores)
    sd = statistics.pstdev(scores)  # population std
    if sd == 0:
        return scores
    upper = m + 3 * sd
    lower = m - 3 * sd

    def clamp_scale(v):
        c = min(upper, max(lower, v))
        return (c - lower) / (upper - lower)

    return [clamp_scale(s) for s in scores]


@beartype
def fuse_results(
    text_docs: List[Doc], embedding_docs: List[Doc], alpha: float
) -> List[Doc]:
    """
    Merges text search results (descending by text rank) with
    embedding results (descending by closeness or inverse distance).
    alpha ~ how much to weigh the embedding score
    """
    # Suppose we stored each doc's "distance" from the embedding query, and
    # for text search we store a rank or negative distance. We'll unify them:
    # Make up a dictionary of doc_id -> text_score, doc_id -> embed_score
    # For example, text_score = -distance if you want bigger = better
    text_scores = {}
    embed_scores = {}
    for doc in text_docs:
        # If you had "rank", you might store doc.distance = rank
        # For demo, let's assume doc.distance is negative... up to you
        text_scores[doc.id] = float(-doc.distance if doc.distance else 0)

    for doc in embedding_docs:
        # Lower distance => better, so we do embed_score = -distance
        embed_scores[doc.id] = float(-doc.distance if doc.distance else 0)

    # Normalize them
    text_vals = list(text_scores.values())
    embed_vals = list(embed_scores.values())
    text_vals_norm = dbsf_normalize(text_vals)
    embed_vals_norm = dbsf_normalize(embed_vals)

    # Map them back
    t_keys = list(text_scores.keys())
    for i, key in enumerate(t_keys):
        text_scores[key] = text_vals_norm[i]
    e_keys = list(embed_scores.keys())
    for i, key in enumerate(e_keys):
        embed_scores[key] = embed_vals_norm[i]

    # Gather all doc IDs
    all_ids = set(text_scores.keys()) | set(embed_scores.keys())

    # Weighted sum => combined
    out = []
    for doc_id in all_ids:
        # text and embed might be missing doc_id => 0
        t_score = text_scores.get(doc_id, 0)
        e_score = embed_scores.get(doc_id, 0)
        combined = alpha * e_score + (1 - alpha) * t_score
        # We'll store final "distance" as -(combined) so bigger combined => smaller distance
        out.append((doc_id, combined))

    # Sort descending by combined
    out.sort(key=lambda x: x[1], reverse=True)

    # Convert to doc objects. We can pick from text_docs or embedding_docs or whichever is found.
    # If present in both, we can merge fields. For simplicity, just pick from text_docs then fallback embedding_docs.

    # Create a quick ID->doc map
    text_map = {d.id: d for d in text_docs}
    embed_map = {d.id: d for d in embedding_docs}

    final_docs = []
    for doc_id, score in out:
        doc = text_map.get(doc_id) or embed_map.get(doc_id)
        doc = doc.model_copy()  # or copy if you are using Pydantic
        doc.distance = float(-score)  # so a higher combined => smaller distance
        final_docs.append(doc)
    return final_docs


@beartype
async def search_docs_hybrid(
    developer_id: UUID,
    text_query: str = "",
    embedding: List[float] = None,
    k: int = 10,
    alpha: float = 0.5,
    owner_type: Literal["user", "agent", "org"] | None = None,
    owner_id: UUID | None = None,
) -> List[Doc]:
    """
    Hybrid text-and-embedding doc search. We get top-K from each approach,
    then fuse them client-side. Adjust concurrency or approach as you like.
    """
    # We'll dispatch two queries in parallel
    # (One full-text, one embedding-based) each limited to K
    tasks = []
    if text_query.strip():
        tasks.append(
            search_docs_by_text(
                developer_id=developer_id,
                query=text_query,
                k=k,
                owner_type=owner_type,
                owner_id=owner_id,
            )
        )
    else:
        tasks.append([])  # no text results if query is empty

    if embedding and any(embedding):
        tasks.append(
            search_docs_by_embedding(
                developer_id=developer_id,
                query_embedding=embedding,
                k=k,
                owner_type=owner_type,
                owner_id=owner_id,
            )
        )
    else:
        tasks.append([])

    # Run concurrently (or sequentially, if you prefer)
    # If you have a 'run_concurrently' from your old code, you can do:
    # text_results, embed_results = await run_concurrently([task1, task2])
    # Otherwise just do them in parallel with e.g. asyncio.gather:
    from asyncio import gather

    text_results, embed_results = await gather(*tasks)

    # fuse them
    fused = fuse_results(text_results, embed_results, alpha)
    # Then pick top K overall
    return fused[:k]

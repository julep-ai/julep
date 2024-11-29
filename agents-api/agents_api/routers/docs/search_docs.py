import time
from typing import Annotated, Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

import numpy as np
from fastapi import Depends

from ...autogen.openapi_model import (
    DocReference,
    DocSearchResponse,
    HybridDocSearchRequest,
    TextOnlyDocSearchRequest,
    VectorDocSearchRequest,
)
from ...dependencies.developer_id import get_developer_id
from ...models.docs.mmr import maximal_marginal_relevance
from ...models.docs.search_docs_by_embedding import search_docs_by_embedding
from ...models.docs.search_docs_by_text import search_docs_by_text
from ...models.docs.search_docs_hybrid import search_docs_hybrid
from .router import router


def get_search_fn_and_params(
    search_params,
) -> Tuple[
    Any, Optional[Dict[str, Union[float, int, str, Dict[str, float], List[float]]]]
]:
    search_fn, params = None, None

    match search_params:
        case TextOnlyDocSearchRequest(
            text=query, limit=k, metadata_filter=metadata_filter
        ):
            search_fn = search_docs_by_text
            params = dict(
                query=query,
                k=k,
                metadata_filter=metadata_filter,
            )

        case VectorDocSearchRequest(
            vector=query_embedding,
            limit=k,
            confidence=confidence,
            metadata_filter=metadata_filter,
        ):
            search_fn = search_docs_by_embedding
            params = dict(
                query_embedding=query_embedding,
                k=k * 3 if search_params.mmr_strength > 0 else k,
                confidence=confidence,
                metadata_filter=metadata_filter,
            )

        case HybridDocSearchRequest(
            text=query,
            vector=query_embedding,
            limit=k,
            confidence=confidence,
            alpha=alpha,
            metadata_filter=metadata_filter,
        ):
            search_fn = search_docs_hybrid
            params = dict(
                query=query,
                query_embedding=query_embedding,
                k=k * 3 if search_params.mmr_strength > 0 else k,
                embed_search_options=dict(confidence=confidence),
                alpha=alpha,
                metadata_filter=metadata_filter,
            )

    return search_fn, params


@router.post("/users/{user_id}/search", tags=["docs"])
async def search_user_docs(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    search_params: (
        TextOnlyDocSearchRequest | VectorDocSearchRequest | HybridDocSearchRequest
    ),
    user_id: UUID,
) -> DocSearchResponse:
    """
    Searches for documents associated with a specific user.

    Parameters:
        x_developer_id (UUID): The unique identifier of the developer associated with the user.
        search_params (TextOnlyDocSearchRequest | VectorDocSearchRequest | HybridDocSearchRequest): The parameters for the search.
        user_id (UUID): The unique identifier of the user associated with the documents.

    Returns:
        DocSearchResponse: The search results.
    """

    # MMR here
    search_fn, params = get_search_fn_and_params(search_params)

    start = time.time()
    docs: list[DocReference] = search_fn(
        developer_id=x_developer_id,
        owners=[("user", user_id)],
        **params,
    )

    if (
        not isinstance(search_params, TextOnlyDocSearchRequest)
        and search_params.mmr_strength > 0
        and len(docs) > search_params.limit
    ):
        indices = maximal_marginal_relevance(
            np.asarray(params["query_embedding"]),
            [doc.snippet.embedding for doc in docs],
            k=search_params.limit,
        )
        docs = [doc for i, doc in enumerate(docs) if i in set(indices)]

    end = time.time()

    time_taken = end - start

    return DocSearchResponse(
        docs=docs,
        time=time_taken,
    )


@router.post("/agents/{agent_id}/search", tags=["docs"])
async def search_agent_docs(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    search_params: (
        TextOnlyDocSearchRequest | VectorDocSearchRequest | HybridDocSearchRequest
    ),
    agent_id: UUID,
) -> DocSearchResponse:
    """
    Searches for documents associated with a specific agent.

    Parameters:
        x_developer_id (UUID): The unique identifier of the developer associated with the agent.
        search_params (TextOnlyDocSearchRequest | VectorDocSearchRequest | HybridDocSearchRequest): The parameters for the search.
        agent_id (UUID): The unique identifier of the agent associated with the documents.

    Returns:
        DocSearchResponse: The search results.
    """

    search_fn, params = get_search_fn_and_params(search_params)

    start = time.time()
    docs: list[DocReference] = search_fn(
        developer_id=x_developer_id,
        owners=[("agent", agent_id)],
        **params,
    )

    if (
        not isinstance(search_params, TextOnlyDocSearchRequest)
        and search_params.mmr_strength > 0
        and len(docs) > search_params.limit
    ):
        indices = maximal_marginal_relevance(
            np.asarray(params["query_embedding"]),
            [doc.snippet.embedding for doc in docs],
            k=search_params.limit,
        )
        docs = [doc for i, doc in enumerate(docs) if i in set(indices)]

    end = time.time()

    time_taken = end - start

    return DocSearchResponse(
        docs=docs,
        time=time_taken,
    )

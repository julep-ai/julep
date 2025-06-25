import time
from typing import Annotated, Any
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
from ...common.utils.get_doc_search import get_search_fn_and_params
from ...common.utils.mmr import apply_mmr_to_docs
from ...dependencies.developer_id import get_developer_id
from ..utils.doc_utils import strip_embeddings
from .router import router


@router.post("/users/{user_id}/search", tags=["docs"])
async def search_user_docs(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    search_params: (TextOnlyDocSearchRequest | VectorDocSearchRequest | HybridDocSearchRequest),
    user_id: UUID,
    connection_pool: Any = None,  # FIXME: Placeholder that should be removed
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

    # Get the search function and params here
    search_fn, params, post_processing = get_search_fn_and_params(search_params)

    include_embeddings = post_processing.get("include_embeddings", True)

    start = time.time()
    # Get the docs here
    docs: list[DocReference] = await search_fn(
        developer_id=x_developer_id,
        owners=[("user", user_id)],
        **params,
    )

    if include_embeddings == False:
        docs = strip_embeddings(docs)

    # Apply MMR if enabled and applicable
    if (
        not isinstance(search_params, TextOnlyDocSearchRequest)
        and len(docs) > search_params.limit
        and search_params.mmr_strength > 0
    ):
        docs = apply_mmr_to_docs(
            docs=docs,
            query_embedding=np.asarray(params["embedding"]),
            limit=search_params.limit,
            mmr_strength=search_params.mmr_strength,
        )

    end = time.time()

    time_taken = end - start

    return DocSearchResponse(
        docs=docs,
        time=max(time_taken, 0.01),
    )


@router.post("/agents/{agent_id}/search", tags=["docs"])
async def search_agent_docs(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    search_params: (TextOnlyDocSearchRequest | VectorDocSearchRequest | HybridDocSearchRequest),
    agent_id: UUID,
    connection_pool: Any = None,  # FIXME: Placeholder that should be removed
) -> DocSearchResponse:
    """
    Searches for documents associated with a specific agent.

    Parameters:
        x_developer_id (UUID): The unique identifier of the developer associated with the agent.
        search_params (TextOnlyDocSearchRequest | VectorDocSearchRequest | HybridDocSearchRequest): The parameters for the search.
        agent_id (UUID): The umnique identifier of the agent associated with the documents.
    Returns:
        DocSearchResponse: The search results.
    """

    # Get the search function and params here
    search_fn, params, post_processing = get_search_fn_and_params(search_params)

    include_embeddings = post_processing.get("include_embeddings", True)

    start = time.time()
    # Get the docs here
    docs: list[DocReference] = await search_fn(
        developer_id=x_developer_id,
        owners=[("agent", agent_id)],
        **params,
    )

    if include_embeddings == False:
        docs = strip_embeddings(docs)

    # Apply MMR if enabled and applicable
    if (
        not isinstance(search_params, TextOnlyDocSearchRequest)
        and len(docs) > search_params.limit
        and search_params.mmr_strength > 0
    ):
        docs = apply_mmr_to_docs(
            docs=docs,
            query_embedding=np.asarray(params["embedding"]),
            limit=search_params.limit,
            mmr_strength=search_params.mmr_strength,
        )

    end = time.time()

    time_taken = end - start

    return DocSearchResponse(
        docs=docs,
        time=max(time_taken, 0.01),
    )

import time
from typing import Annotated, Any, Dict, List, Optional, Tuple, Union

from fastapi import Depends
from pydantic import UUID4

from ...autogen.openapi_model import (
    DocSearchResponse,
    HybridDocSearchRequest,
    TextOnlyDocSearchRequest,
    VectorDocSearchRequest,
)
from ...dependencies.developer_id import get_developer_id
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
        case TextOnlyDocSearchRequest(text=query, limit=k):
            search_fn = search_docs_by_text
            params = dict(
                query=query,
                k=k,
            )

        case VectorDocSearchRequest(
            vector=query_embedding, limit=k, confidence=confidence
        ):
            search_fn = search_docs_by_embedding
            params = dict(
                query_embedding=query_embedding,
                k=k,
                confidence=confidence,
            )

        case HybridDocSearchRequest(
            text=query,
            vector=query_embedding,
            limit=k,
            confidence=confidence,
            alpha=alpha,
        ):
            search_fn = search_docs_hybrid
            params = dict(
                query=query,
                query_embedding=query_embedding,
                k=k,
                embed_search_options=dict(confidence=confidence),
                alpha=alpha,
            )

    return search_fn, params


@router.post("/users/{user_id}/search", tags=["docs"])
async def search_user_docs(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    search_params: (
        TextOnlyDocSearchRequest | VectorDocSearchRequest | HybridDocSearchRequest
    ),
    user_id: UUID4,
) -> DocSearchResponse:
    search_fn, params = get_search_fn_and_params(search_params)

    start = time.time()
    docs = search_fn(
        developer_id=x_developer_id,
        owners=[("user", user_id)],
        **params,
    )

    end = time.time()

    time_taken = end - start

    return DocSearchResponse(
        docs=docs,
        time=time_taken,
    )


@router.post("/agents/{agent_id}/search", tags=["docs"])
async def search_agent_docs(
    x_developer_id: Annotated[UUID4, Depends(get_developer_id)],
    search_params: (
        TextOnlyDocSearchRequest | VectorDocSearchRequest | HybridDocSearchRequest
    ),
    agent_id: UUID4,
) -> DocSearchResponse:
    search_fn, params = get_search_fn_and_params(search_params)

    start = time.time()
    docs = search_fn(
        developer_id=x_developer_id,
        owners=[("agent", agent_id)],
        **params,
    )

    end = time.time()

    time_taken = end - start

    return DocSearchResponse(
        docs=docs,
        time=time_taken,
    )

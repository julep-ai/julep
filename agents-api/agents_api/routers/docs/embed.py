from typing import Annotated
from uuid import UUID

from fastapi import Depends

import agents_api.clients.vertexai as embedder

from ...autogen.openapi_model import (
    EmbedQueryRequest,
    EmbedQueryResponse,
)
from ...dependencies.developer_id import get_developer_id
from .router import router


@router.post("/embed", tags=["docs"])
async def embed(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    data: EmbedQueryRequest,
) -> EmbedQueryResponse:
    text_to_embed: str | list[str] = data.text
    text_to_embed: list[str] = (
        [text_to_embed] if isinstance(text_to_embed, str) else text_to_embed
    )

    vectors = await embedder.embed(inputs=text_to_embed)

    return EmbedQueryResponse(vectors=vectors)

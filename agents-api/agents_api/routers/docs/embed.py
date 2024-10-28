from typing import Annotated
from uuid import UUID

from fastapi import Depends

from ...autogen.openapi_model import (
    EmbedQueryResponse,
    MultipleEmbedQueryRequest,
    SingleEmbedQueryRequest,
)
from ...clients import litellm
from ...dependencies.developer_id import get_developer_id
from .router import router


@router.post("/embed", tags=["docs"])
async def embed(
    x_developer_id: Annotated[UUID, Depends(get_developer_id)],
    data: SingleEmbedQueryRequest | MultipleEmbedQueryRequest,
) -> EmbedQueryResponse:
    text_to_embed: str | list[str] = data.text
    text_to_embed: list[str] = (
        [text_to_embed] if isinstance(text_to_embed, str) else text_to_embed
    )
    vectors = await litellm.aembedding(
        inputs=[data.embed_instruction + text for text in text_to_embed]
    )

    return EmbedQueryResponse(vectors=vectors)

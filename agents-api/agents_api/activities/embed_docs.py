import asyncio
import operator
from functools import reduce
from itertools import batched

from beartype import beartype
from temporalio import activity

from ..clients import cozo, litellm
from ..common.storage_handler import auto_blob_store
from ..env import testing
from ..models.docs.embed_snippets import embed_snippets as embed_snippets_query
from .types import EmbedDocsPayload


@auto_blob_store
@beartype
async def embed_docs(
    payload: EmbedDocsPayload, cozo_client=None, max_batch_size: int = 100
) -> None:
    indices, snippets = list(zip(*enumerate(payload.content)))
    batched_snippets = batched(snippets, max_batch_size)
    embed_instruction: str = payload.embed_instruction or ""
    title: str = payload.title or ""

    async def embed_batch(snippets):
        return await litellm.aembedding(
            inputs=[
                (
                    embed_instruction + (title + "\n\n" + snippet) if title else snippet
                ).strip()
                for snippet in snippets
            ]
        )

    embeddings = reduce(
        operator.add,
        await asyncio.gather(*[embed_batch(snippets) for snippets in batched_snippets]),
    )

    embed_snippets_query(
        developer_id=payload.developer_id,
        doc_id=payload.doc_id,
        snippet_indices=indices,
        embeddings=embeddings,
        client=cozo_client or cozo.get_cozo_client(),
    )


async def mock_embed_docs(
    payload: EmbedDocsPayload, cozo_client=None, max_batch_size=100
) -> None:
    # Does nothing
    return None


embed_docs = activity.defn(name="embed_docs")(
    embed_docs if not testing else mock_embed_docs
)

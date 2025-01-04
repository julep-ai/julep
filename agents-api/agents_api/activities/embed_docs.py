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


@auto_blob_store(deep=True)
@beartype
async def embed_docs(
    payload: EmbedDocsPayload, cozo_client=None, max_batch_size: int = 100
) -> None:
    # Create batches of both indices and snippets together
    indexed_snippets = list(enumerate(payload.content))
    # Batch snippets into groups of max_batch_size for parallel processing
    batched_indexed_snippets = list(batched(indexed_snippets, max_batch_size))
    # Get embedding instruction and title from payload, defaulting to empty strings
    embed_instruction: str = payload.embed_instruction or ""
    title: str = payload.title or ""

    # Helper function to embed a batch of snippets
    async def embed_batch(indexed_batch):
        # Split indices and snippets for the batch
        batch_indices, batch_snippets = zip(*indexed_batch)
        embeddings = await litellm.aembedding(
            inputs=[
                ((title + "\n\n" + snippet) if title else snippet).strip()
                for snippet in batch_snippets
            ],
            embed_instruction=embed_instruction,
        )
        return list(zip(batch_indices, embeddings))

    # Gather embeddings with their corresponding indices
    indexed_embeddings = reduce(
        operator.add,
        await asyncio.gather(
            *[embed_batch(batch) for batch in batched_indexed_snippets]
        ),
    )

    # Split indices and embeddings after all batches are processed
    indices, embeddings = zip(*indexed_embeddings)

    # Convert to lists since embed_snippets_query expects list types
    indices = list(indices)
    embeddings = list(embeddings)

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

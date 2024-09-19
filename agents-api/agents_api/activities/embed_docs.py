from beartype import beartype
from temporalio import activity

from ..clients import cozo
from ..clients import vertexai as embedder
from ..env import testing
from ..models.docs.embed_snippets import embed_snippets as embed_snippets_query
from .types import EmbedDocsPayload


@beartype
async def embed_docs(payload: EmbedDocsPayload, cozo_client=None) -> None:
    indices, snippets = list(zip(*enumerate(payload.content)))
    embed_instruction: str = payload.embed_instruction or ""
    title: str = payload.title or ""

    embeddings = await embedder.embed(
        [
            (
                embed_instruction + (title + "\n\n" + snippet) if title else snippet
            ).strip()
            for snippet in snippets
        ]
    )

    embed_snippets_query(
        developer_id=payload.developer_id,
        doc_id=payload.doc_id,
        snippet_indices=indices,
        embeddings=embeddings,
        client=cozo_client or cozo.get_cozo_client(),
    )


async def mock_embed_docs(payload: EmbedDocsPayload, cozo_client=None) -> None:
    # Does nothing
    return None


embed_docs = activity.defn(name="embed_docs")(
    embed_docs if not testing else mock_embed_docs
)

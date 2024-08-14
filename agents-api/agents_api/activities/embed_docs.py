from uuid import UUID

from temporalio import activity

from agents_api.clients import embed as embedder
from agents_api.clients.cozo import get_cozo_client
from agents_api.models.docs.embed_snippets import embed_snippets as embed_snippets_query

snippet_embed_instruction = "Encode this passage for retrieval: "


@activity.defn
async def embed_docs(
    developer_id: UUID,
    doc_id: UUID,
    title: str,
    content: list[str],
    include_title: bool = True,
    cozo_client=None,
) -> None:
    indices, snippets = list(zip(*enumerate(content)))

    embeddings = await embedder.embed(
        [
            {
                "instruction": snippet_embed_instruction,
                "text": (title + "\n\n" + snippet) if include_title else snippet,
            }
            for snippet in snippets
        ]
    )

    embed_snippets_query(
        developer_id=developer_id,
        doc_id=doc_id,
        snippet_indices=indices,
        embeddings=embeddings,
        client=cozo_client or get_cozo_client(),
    )

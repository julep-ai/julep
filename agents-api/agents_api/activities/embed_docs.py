from pydantic import UUID4
from temporalio import activity

from agents_api.clients.embed import embed
from agents_api.models.docs.embed_snippets import embed_snippets as embed_snippets_query

snippet_embed_instruction = "Encode this passage for retrieval: "


@activity.defn
async def embed_docs(doc_id: UUID4, title: str, content: list[str]) -> None:
    indices, snippets = list(zip(*enumerate(content)))
    embeddings = await embed(
        [
            {
                "instruction": snippet_embed_instruction,
                "text": title + "\n\n" + snippet,
            }
            for snippet in snippets
        ]
    )

    embed_snippets_query(
        doc_id=doc_id,
        snippet_indices=indices,
        embeddings=embeddings,
    )

from pydantic import UUID4
from temporalio import activity
from agents_api.env import embedding_model_id
from agents_api.models.docs.embed_docs import (
    embed_docs_snippets_query,
)
from agents_api.embed_models_registry import EmbeddingModel


snippet_embed_instruction = "Encode this passage for retrieval: "


@activity.defn
async def embed_docs(doc_id: UUID4, title: str, content: list[str]) -> None:
    indices, snippets = list(zip(*enumerate(content)))
    model = EmbeddingModel.from_model_name(embedding_model_id)
    embeddings = await model.embed(
        [
            {
                "instruction": snippet_embed_instruction,
                "text": title + "\n\n" + snippet,
            }
            for snippet in snippets
        ]
    )

    embed_docs_snippets_query(
        doc_id=doc_id,
        snippet_indices=indices,
        embeddings=embeddings,
    )

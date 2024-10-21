from beartype import beartype
from temporalio import activity

from ..clients import cozo, litellm
from ..env import testing
from ..models.docs.embed_snippets import embed_snippets as embed_snippets_query
from .types import EmbedDocsPayload


@beartype

# FEEDBACK[@Bhabuk10]: Great use of the `beartype` decorator to ensure type checking
# at runtime. However, if the project allows for stricter static type checking, consider using 
# Python's `mypy` as well. It can complement `beartype` and catch more issues during development.

async def embed_docs(payload: EmbedDocsPayload, cozo_client=None) -> None:
    indices, snippets = list(zip(*enumerate(payload.content)))

    # QUESTION[@Bhabuk10]: What is the rationale for using `enumerate` here?
    # Is the index being used later on, or is it necessary in this context? 
    # If indices are always needed for snippets, a comment explaining their use would help clarify.

    embed_instruction: str = payload.embed_instruction or ""
    title: str = payload.title or ""

    embeddings = await litellm.aembedding(
        inputs=[
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
# QUESTION[@Bhabuk10]: What is the purpose of this conditional? 
# Should the code switch between `embed_docs` and `mock_embed_docs` based purely on the `testing` variable?
# Clarification on the conditions under which this switch happens would be helpful.

# FEEDBACK[@Bhabuk10]: Consider improving the clarity of the conditional that switches 
# between `embed_docs` and `mock_embed_docs`. It may be better to centralize the testing condition 
# logic so that it's easier to extend or modify in the future.
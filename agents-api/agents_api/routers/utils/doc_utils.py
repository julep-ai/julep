from agents_api.autogen.openapi_model import DocReference
from beartype import beartype

@beartype
def strip_embeddings(docs: list[DocReference] | DocReference) -> list[DocReference] | DocReference:
    if isinstance(docs, list):
        docs = [strip_embeddings(doc) for doc in docs]
    else:
        docs.snippet.embedding = None
    return docs
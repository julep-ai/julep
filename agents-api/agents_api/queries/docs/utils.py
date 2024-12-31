import ast


def transform_to_doc_reference(d: dict) -> dict:
    id = d.pop("doc_id")
    content = d.pop("content")
    index = d.pop("index")

    embedding = d.pop("embedding")

    try:
        # Embeddings are retreived as a string, so we need to evaluate it
        embedding = ast.literal_eval(embedding)
    except Exception as e:
        msg = f"Error evaluating embeddings: {e}"
        raise ValueError(msg)

    owner = {
        "id": d.pop("owner_id"),
        "role": d.pop("owner_type"),
    }
    snippet = {
        "content": content,
        "index": index,
        "embedding": embedding,
    }
    metadata = d.pop("metadata")

    return {
        "id": id,
        "owner": owner,
        "snippet": snippet,
        "metadata": metadata,
        **d,
    }

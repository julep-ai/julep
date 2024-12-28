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
        raise ValueError(f"Error evaluating embeddings: {e}")

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

    transformed_data = {
        "id": id,
        "owner": owner,
        "snippet": snippet,
        "metadata": metadata,
        **d,
    }

    return transformed_data

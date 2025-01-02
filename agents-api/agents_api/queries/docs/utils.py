import json


def transform_to_doc_reference(d: dict) -> dict:
    id = d.pop("doc_id")
    content = d.pop("content")
    index = d.pop("index")

    # Convert embedding array string to list of floats if present
    if d["embedding"] is not None:
        try:
            embedding = json.loads(d["embedding"])
        except Exception as e:
            msg = f"Error evaluating embeddings: {e}"
            raise ValueError(msg)

    else:
        embedding = None

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

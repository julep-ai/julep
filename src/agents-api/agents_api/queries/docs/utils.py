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
        **d,
        "id": id,
        "owner": owner,
        "snippet": snippet,
        "metadata": metadata,
    }


def transform_doc(d: dict) -> dict:
    content = d["content"]

    embeddings = d.get("embeddings") or []

    if embeddings:
        if isinstance(embeddings, str):
            embeddings = json.loads(embeddings) if embeddings.strip() else None
        elif isinstance(embeddings, list) and all(isinstance(e, str) for e in embeddings):
            embeddings = [json.loads(e) for e in embeddings if e.strip()]

    if embeddings and all((e is None) for e in embeddings):
        embeddings = None

    return {
        **d,
        "id": d["doc_id"],
        "content": content,
        "embeddings": embeddings,
    }

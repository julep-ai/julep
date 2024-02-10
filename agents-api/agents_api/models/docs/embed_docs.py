import json
from uuid import UUID


def embed_docs_snippets_query(
    doc_id: UUID,
    snippet_indices: list[int],
    embeddings: list[list[float]],
):
    doc_id = str(doc_id)
    assert len(snippet_indices) == len(embeddings)

    records = "\n".join(
        [
            f'[to_uuid("{doc_id}"), {snippet_idx}, vec({json.dumps(embedding)})],'
            for snippet_idx, embedding in zip(snippet_indices, embeddings)
        ]
    )

    return f"""
    {{
        ?[doc_id, snippet_idx, embedding] <- [
            {records}
        ]

        :update information_snippets {{
            doc_id,
            snippet_idx,
            embedding,
        }}
        :returning
    }}"""

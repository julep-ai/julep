import json
from uuid import UUID


def embed_additional_info_snippets_query(
    additional_info_id: UUID,
    snippet_indices: list[int],
    embeddings: list[list[float]],
):
    additional_info_id = str(additional_info_id)
    assert len(snippet_indices) == len(embeddings)

    records = "\n".join(
        [
            f'[to_uuid("{additional_info_id}"), {snippet_idx}, vec({json.dumps(embedding)})],'
            for snippet_idx, embedding in zip(snippet_indices, embeddings)
        ]
    )

    return f"""
    {{
        ?[additional_info_id, snippet_idx, embedding] <- [
            {records}
        ]

        :update information_snippets {{
            additional_info_id,
            snippet_idx,
            embedding,
        }}
        :returning
    }}"""

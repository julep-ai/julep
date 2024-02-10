import json
from typing import Literal
from uuid import UUID


def search_docs_snippets_by_embedding_query(
    owner_type: Literal["user", "agent"],
    owner_id: UUID,
    query_embedding: list[float],
    k: int = 3,
    confidence: float = 0.8,
):
    owner_id = str(owner_id)
    radius: float = 1.0 - confidence

    return f"""
    {{
        input[
            {owner_type}_id,
            query_embedding,
        ] <- [[
            to_uuid("{owner_id}"),
            vec({json.dumps(query_embedding)}),
        ]]

        candidate[
            doc_id
        ] := input[{owner_type}_id, _],
            *{owner_type}_docs {{
                {owner_type}_id,
                doc_id
            }}

        ?[
            {owner_type}_id,
            doc_id,
            title,
            snippet,
            snippet_idx,
            distance,
            vector,
        ] := input[{owner_type}_id, query_embedding],
            candidate[doc_id],
            ~information_snippets:embedding_space {{
                doc_id,
                snippet_idx,
                title,
                snippet |
                query: query_embedding,
                k: {k},
                ef: 128,
                radius: {radius},
                bind_distance: distance,
                bind_vector: vector,
            }}

        :sort distance
    }}"""

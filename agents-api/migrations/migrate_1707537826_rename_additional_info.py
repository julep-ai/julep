# /usr/bin/env python3

MIGRATION_ID = "rename_additional_info"
CREATED_AT = 1707537826.539182

rename_agent_doc_id = dict(
    up="""
    ?[agent_id, doc_id, created_at] :=
        *agent_additional_info{
            agent_id,
            additional_info_id: doc_id,
            created_at,
        }

    :replace agent_additional_info {
        agent_id: Uuid,
        doc_id: Uuid
        =>
        created_at: Float default now(),
    }
    """,
    down="""
    ?[agent_id, additional_info_id, created_at] :=
        *agent_additional_info{
            agent_id,
            doc_id: additional_info_id,
            created_at,
        }

    :replace agent_additional_info {
        agent_id: Uuid,
        additional_info_id: Uuid
        =>
        created_at: Float default now(),
    }
    """,
)


rename_user_doc_id = dict(
    up="""
    ?[user_id, doc_id, created_at] :=
        *user_additional_info{
            user_id,
            additional_info_id: doc_id,
            created_at,
        }

    :replace user_additional_info {
        user_id: Uuid,
        doc_id: Uuid
        =>
        created_at: Float default now(),
    }
    """,
    down="""
    ?[user_id, additional_info_id, created_at] :=
        *user_additional_info{
            user_id,
            doc_id: additional_info_id,
            created_at,
        }

    :replace user_additional_info {
        user_id: Uuid,
        additional_info_id: Uuid
        =>
        created_at: Float default now(),
    }
    """,
)

# See: https://github.com/nmslib/hnswlib/blob/master/ALGO_PARAMS.md
information_snippets_hnsw_index = dict(
    up="""
    ::hnsw create information_snippets:embedding_space {
        fields: [embedding],
        filter: !is_null(embedding),
        dim: 768,
        distance: Cosine,
        m: 64,
        ef_construction: 256,
        extend_candidates: false,
        keep_pruned_connections: false,
    }
    """,
    down="""
    ::hnsw drop information_snippets:embedding_space
    """,
)

# See: https://docs.cozodb.org/en/latest/vector.html#full-text-search-fts
information_snippets_fts_index = dict(
    up="""
    ::fts create information_snippets:fts {
        extractor: concat(title, ' ', snippet),
        tokenizer: Simple,
        filters: [Lowercase, Stemmer('english'), Stopwords('en')],
    }
    """,
    down="""
    ::fts drop information_snippets:fts
    """,
)

drop_information_snippets_hnsw_index = {
    "up": information_snippets_hnsw_index["down"],
    "down": information_snippets_hnsw_index["up"],
}


drop_information_snippets_fts_index = {
    "up": information_snippets_fts_index["down"],
    "down": information_snippets_fts_index["up"],
}


rename_information_snippets_doc_id = dict(
    up="""
    ?[
        doc_id,
        snippet_idx,
        title,
        snippet,
        embed_instruction,
        embedding,
    ] :=
        *information_snippets{
            snippet_idx,
            title,
            snippet,
            embed_instruction,
            embedding,
            additional_info_id: doc_id,
        }

    :replace information_snippets {
        doc_id: Uuid,
        snippet_idx: Int,
        =>
        title: String,
        snippet: String,
        embed_instruction: String default 'Encode this passage for retrieval: ',
        embedding: <F32; 768>? default null,
    }
    """,
    down="""
    ?[
        additional_info_id,
        snippet_idx,
        title,
        snippet,
        embed_instruction,
        embedding,
    ] :=
        *information_snippets{
            snippet_idx,
            title,
            snippet,
            embed_instruction,
            embedding,
            doc_id: additional_info_id,
        }

    :replace information_snippets {
        additional_info_id: Uuid,
        snippet_idx: Int,
        =>
        title: String,
        snippet: String,
        embed_instruction: String default 'Encode this passage for retrieval: ',
        embedding: <F32; 768>? default null,
    }
    """,
)

rename_relations = dict(
    up="""
    ::rename
      agent_additional_info -> agent_docs,
      user_additional_info -> user_docs
    """,
    down="""
    ::rename
      agent_docs -> agent_additional_info,
      user_docs -> user_additional_info
    """,
)


queries_to_run = [
    rename_agent_doc_id,
    rename_user_doc_id,
    drop_information_snippets_hnsw_index,
    drop_information_snippets_fts_index,
    rename_information_snippets_doc_id,
    information_snippets_hnsw_index,
    information_snippets_fts_index,
    rename_relations,
]


def run(client, *queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"

    client.run(query)


def up(client):
    run(client, *[q["up"] for q in queries_to_run])


def down(client):
    run(client, *[q["down"] for q in reversed(queries_to_run)])

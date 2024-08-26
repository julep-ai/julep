# /usr/bin/env python3

MIGRATION_ID = "unify_owner_doc_relations"
CREATED_AT = 1722710530.126563

create_docs_relations_query = dict(
    up="""
    :create docs {
        owner_type: String,
        owner_id: Uuid,
        doc_id: Uuid,
        =>
        title: String,
        created_at: Float default now(),
        metadata: Json default {},
    }
    """,
    down="::remove docs",
)

remove_user_docs_table = dict(
    up="""
    doc_title[doc_id, unique(title)] :=
        *snippets {
            doc_id,
            title,
        }

    ?[owner_type, owner_id, doc_id, title, created_at, metadata] :=
        owner_type = "user",
        *user_docs {
            user_id: owner_id,
            doc_id,
            created_at,
            metadata,
        },
        doc_title[doc_id, title]

    :insert docs {
        owner_type,
        owner_id,
        doc_id,
        title,
        created_at,
        metadata,
    }

    } {  # <-- this is just a separator between the two queries
    ::remove user_docs
    """,
    down="""
    :create user_docs {
        user_id: Uuid,
        doc_id: Uuid
        =>
        created_at: Float default now(),
        metadata: Json default {},
    }
    """,
)

remove_agent_docs_table = dict(
    up=remove_user_docs_table["up"].replace("user", "agent"),
    down=remove_user_docs_table["down"].replace("user", "agent"),
)

# See: https://github.com/nmslib/hnswlib/blob/master/ALGO_PARAMS.md
snippets_hnsw_index = dict(
    up="""
    ::hnsw create snippets:embedding_space {
        fields: [embedding],
        filter: !is_null(embedding),
        dim: 1024,
        distance: Cosine,
        m: 64,
        ef_construction: 256,
        extend_candidates: true,
        keep_pruned_connections: false,
    }
    """,
    down="""
    ::hnsw drop snippets:embedding_space
    """,
)

# See: https://docs.cozodb.org/en/latest/vector.html#full-text-search-fts
snippets_fts_index = dict(
    up="""
    ::fts create snippets:fts {
        extractor: content,
        tokenizer: Simple,
        filters: [Lowercase, Stemmer('english'), Stopwords('en')],
    }
    """,
    down="""
    ::fts drop snippets:fts
    """,
)

temp_rename_snippets_table = dict(
    up="""
    ::rename snippets -> information_snippets
    """,
    down="""
    ::rename information_snippets -> snippets
    """,
)

temp_rename_snippets_table_back = dict(
    up=temp_rename_snippets_table["down"],
    down=temp_rename_snippets_table["up"],
)

drop_snippets_hnsw_index = {
    "up": snippets_hnsw_index["down"].replace("snippets:", "information_snippets:"),
    "down": snippets_hnsw_index["up"].replace("snippets:", "information_snippets:"),
}

drop_snippets_fts_index = dict(
    up="""
    ::fts drop information_snippets:fts
    """,
    down="""
    ::fts create information_snippets:fts {
        extractor: concat(title, ' ', snippet),
        tokenizer: Simple,
        filters: [Lowercase, Stemmer('english'), Stopwords('en')],
    }
    """,
)


remove_title_from_snippets_table = dict(
    up="""
    ?[doc_id, index, content, embedding] :=
        *snippets {
            doc_id,
            snippet_idx: index,
            snippet: content,
            embedding,
        }

     :replace snippets {
        doc_id: Uuid,
        index: Int,
        =>
        content: String,
        embedding: <F32; 1024>? default null,
    }
    """,
    down="""
    ?[doc_id, snippet_idx, title, snippet, embedding] :=
        *snippets {
            doc_id,
            index: snippet_idx,
            content: snippet,
            embedding,
        },
        *docs {
            doc_id,
            title,
        }

    :replace snippets {
        doc_id: Uuid,
        snippet_idx: Int,
        =>
        title: String,
        snippet: String,
        embed_instruction: String default 'Encode this passage for retrieval: ',
        embedding: <F32; 1024>? default null,
    }
    """,
)

queries = [
    create_docs_relations_query,
    remove_user_docs_table,
    remove_agent_docs_table,
    temp_rename_snippets_table,  # Because of a bug in Cozo
    drop_snippets_hnsw_index,
    drop_snippets_fts_index,
    temp_rename_snippets_table_back,  # Because of a bug in Cozo
    remove_title_from_snippets_table,
    snippets_fts_index,
    snippets_hnsw_index,
]


def run(client, queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"

    client.run(query)


def up(client):
    run(client, [q["up"] for q in queries])


def down(client):
    run(client, [q["down"] for q in reversed(queries)])

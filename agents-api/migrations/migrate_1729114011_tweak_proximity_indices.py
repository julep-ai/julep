# /usr/bin/env python3

MIGRATION_ID = "tweak_proximity_indices"
CREATED_AT = 1729114011.022733


def run(client, *queries):
    joiner = "}\n\n{"

    query = joiner.join(queries)
    query = f"{{\n{query}\n}}"
    client.run(query)


drop_snippets_lsh_index = dict(
    up="""
    ::lsh drop snippets:lsh
    """,
    down="""
    ::lsh create snippets:lsh {
        extractor: content,
        tokenizer: Simple,
        filters: [Stopwords('en')],
        n_perm: 200,
        target_threshold: 0.9,
        n_gram: 3,
        false_positive_weight: 1.0,
        false_negative_weight: 1.0,
    }
    """,
)

snippets_lsh_index = dict(
    up="""
    ::lsh create snippets:lsh {
        extractor: content,
        tokenizer: Simple,
        filters: [Lowercase, AsciiFolding, Stemmer('english'), Stopwords('en')],
        n_perm: 200,
        target_threshold: 0.5,
        n_gram: 2,
        false_positive_weight: 1.0,
        false_negative_weight: 1.0,
    }
    """,
    down="""
    ::lsh drop snippets:lsh
    """,
)

# See: https://docs.cozodb.org/en/latest/vector.html#full-text-search-fts
drop_snippets_fts_index = dict(
    down="""
    ::fts create snippets:fts {
        extractor: content,
        tokenizer: Simple,
        filters: [Lowercase, Stemmer('english'), Stopwords('en')],
    }
    """,
    up="""
    ::fts drop snippets:fts
    """,
)

# See: https://docs.cozodb.org/en/latest/vector.html#full-text-search-fts
snippets_fts_index = dict(
    up="""
    ::fts create snippets:fts {
        extractor: content,
        tokenizer: Simple,
        filters: [Lowercase, AsciiFolding, Stemmer('english'), Stopwords('en')],
    }
    """,
    down="""
    ::fts drop snippets:fts
    """,
)

queries_to_run = [
    drop_snippets_lsh_index,
    drop_snippets_fts_index,
    snippets_lsh_index,
    snippets_fts_index,
]


def up(client):
    run(client, *[q["up"] for q in queries_to_run])


def down(client):
    run(client, *[q["down"] for q in reversed(queries_to_run)])

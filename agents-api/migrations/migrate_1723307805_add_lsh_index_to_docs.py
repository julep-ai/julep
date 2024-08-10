#/usr/bin/env python3

MIGRATION_ID = "add_lsh_index_to_docs"
CREATED_AT = 1723307805.007054

# See: https://docs.cozodb.org/en/latest/vector.html#full-text-search-fts
snippets_lsh_index = dict(
    up="""
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
    down="""
    ::lsh drop snippets:lsh
    """,
)

queries = [
    snippets_lsh_index,
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

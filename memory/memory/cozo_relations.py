from .cozo import client

relation_defs = """
embedding_models {
    name: String,
    dimensions: Int,
    requires_instruction: Bool default false,
    provider: String? default null,
}

###

lm_cache {
    chatml_xxhash64: String,
    model: String,
    chatml: Json,
    params: Json default {},
    expires_at: Float? default null,
    =>
    response: Json,
    embedding: <F32; 768>
}

###

conceptnet {
    concept_id: Uuid,
    concept: String,
    description: String default "",
    embedding: <F32; 768>,
}

###

entities {
    entity_id: Uuid,
    name: String,
    character_id: Uuid,
    description: String default "",
}

###

relations {
    subject: Uuid,
    subject_type: String,
    relation: String,
    object: Uuid,
    object_type: String,
    =>
    weight: Float default 1.0,
}

###

characters {
    character_id: Uuid,
    name: String,
    is_human: Bool default false,
    updated_at: Validity default [floor(now()), true],
    =>
    about: String default "",
    metadata: Json default {},
    model: String? default null,
}

###

sessions {
    session_id: Uuid,
    happened_at: Float default now(),
    updated_at: Validity default [floor(now()), true],
    =>
    situation: String,
    summary: String? default null,
    metadata: Json default {},
}

###

session_characters {
    session_id: Uuid,
    character_id: Uuid,
}

###

entries {
    session_id: Uuid,
    role: String,
    name: String? default null,
    updated_at: Validity default [floor(now()), true],
    =>
    content: String,
    character_id: Uuid? default null,
    sentiment: Float? default null,
}

###

episodes {
    episode_id: Uuid,
    character_id: Uuid,
    summary: String,
    happened_at: Float default now(),
    last_accessed_at: Validity default [floor(now()), true],
    =>
    parent_episode: Uuid? default null,
    aspects: [(String, Float, String, String)] default [],
    duration: Float default 0,
    embedding: <F32; 768>,
}

###

users {
    email: String,
    character_id: Uuid,
    =>
    assistant_id: Uuid,
}

###

beliefs {
    belief_id: Uuid,
    character_id: Uuid,
    belief: String,
    updated_at: Validity default [floor(now()), true],
    =>
    details: String default "",
    parent_belief_id: Uuid? default null,
    valence: Float default 0,
    aspects: [(String, Float, String, String)] default [],
    belief_embedding: <F32; 768>,
    details_embedding: <F32; 768>,
}

###

doc_similarities_768 {
    doc1: <F32; 768>,
    doc2: <F32; 768>,
    =>
    similarity: Float,
}

""".split(
    "###"
)

hnsw_indices_defs = """
lm_cache:embedding_space {
    dim: 768,
    m: 50,
    dtype: F32,
    fields: [embedding],
    distance: Cosine,
    ef_construction: 200,
    extend_candidates: false,
    keep_pruned_connections: false,
}

###

beliefs:embedding_space {
    dim: 768,
    m: 50,
    dtype: F32,
    fields: [belief_embedding, details_embedding],
    distance: Cosine,
    ef_construction: 200,
    extend_candidates: false,
    keep_pruned_connections: false,
}

###

conceptnet:embedding_space {
    dim: 768,
    m: 50,
    dtype: F32,
    fields: embedding,
    distance: Cosine,
    ef_construction: 200,
    extend_candidates: false,
    keep_pruned_connections: false,
}

###

episodes:embedding_space {
    dim: 768,
    m: 50,
    dtype: F32,
    fields: [embedding],
    distance: Cosine,
    filter: !is_null(embedding),
    ef_construction: 200,
    extend_candidates: false,
    keep_pruned_connections: false,
}

""".split(
    "###"
)


lsh_indices_defs = """

conceptnet:concept {
    extractor: concept,
    tokenizer: Simple,
    n_perm: 200,
    target_threshold: 0.8,
    n_gram: 3,
    false_positive_weight: 1.0,
    false_negative_weight: 1.0,
}

###

entities:name {
    extractor: name,
    tokenizer: Simple,
    n_perm: 200,
    target_threshold: 0.8,
    n_gram: 5,
    false_positive_weight: 1.0,
    false_negative_weight: 1.0,
}

###

characters:name {
    extractor: name,
    tokenizer: Simple,
    n_perm: 50,
    target_threshold: 0.8,
    n_gram: 3,
    false_positive_weight: 1.0,
    false_negative_weight: 1.0,
}

""".split(
    "###"
)

fts_indices_defs = """
sessions:summary {
    extractor: summary,
    extract_filter: !is_null(summary),
    tokenizer: Simple,
    filters: [AsciiFolding, AlphaNumOnly, Lowercase, Stemmer('english'), Stopwords('en')],
}

###

beliefs:summary {
    extractor: belief ++ " " ++ details,
    tokenizer: Simple,
    filters: [AsciiFolding, AlphaNumOnly, Lowercase, Stemmer('english'), Stopwords('en')],
}

###

episodes:summary {
    extractor: summary,
    extract_filter: !is_null(summary),
    tokenizer: Simple,
    filters: [AsciiFolding, AlphaNumOnly, Lowercase, Stemmer('english'), Stopwords('en')],
}

###

characters:about {
    extractor: about,
    extract_filter: about != "",
    tokenizer: Simple,
    filters: [AsciiFolding, Lowercase, Stemmer('english'), Stopwords('en')],
}

""".split(
    "###"
)

trigger_defs = """
conceptnet on put {
    ?[doc1, doc2, similarity] := _new[_, _, _, doc2],
                                 *conceptnet{embedding: doc1},
                                 norm1 = l2_normalize(doc1),
                                 norm2 = l2_normalize(doc2),
                                 similarity = cos_dist(norm1, norm2)

    :put doc_similarities_768{doc1, doc2, similarity}
}

###

beliefs on put {
    ?[doc1, doc2, similarity] := _new[_, _, _, doc2],
                                 *beliefs{belief_embedding: doc1},
                                 norm1 = l2_normalize(doc1),
                                 norm2 = l2_normalize(doc2),
                                 similarity = cos_dist(norm1, norm2)

    ?[doc1, doc2, similarity] := _new[_, _, _, doc2],
                                 *beliefs{details_embedding: doc1},
                                 norm1 = l2_normalize(doc1),
                                 norm2 = l2_normalize(doc2),
                                 similarity = cos_dist(norm1, norm2)

    :put doc_similarities_768{doc1, doc2, similarity}
}

###

episodes on put {
    ?[doc1, doc2, similarity] := _new[_, _, _, doc2],
                                 *episodes{embedding: doc1},
                                 norm1 = l2_normalize(doc1),
                                 norm2 = l2_normalize(doc2),
                                 similarity = cos_dist(norm1, norm2)

    :put doc_similarities_768{doc1, doc2, similarity}
}
"""


def run_def_op(defn: str, prefix: str, echo: bool = False):
    op = f"{prefix} {defn.strip()}"
    echo and print(f"Running {op}")
    return client.run(op)


def ensure_relations(echo: bool = False):
    """FIXME: NOT WORKING"""
    for defn in relation_defs:
        run_def_op(defn, "?[a] <- [[1]]\n:ensure", echo)
        echo and print("---")


def create_relations(echo: bool = False):
    for defn in relation_defs:
        run_def_op(defn, ":create", echo)
        echo and print("---")


def create_triggers(echo: bool = False):
    for defn in trigger_defs:
        run_def_op(defn, "::set_triggers", echo)
        echo and print("---")


def create_indices(echo: bool = False):
    for defn in hnsw_indices_defs:
        run_def_op(defn, "::hnsw create", echo)
        echo and print("---")

    for defn in lsh_indices_defs:
        run_def_op(defn, "::lsh create", echo)
        echo and print("---")

    for defn in fts_indices_defs:
        run_def_op(defn, "::fts create", echo)
        echo and print("---")


def create_all(echo: bool = False):
    create_relations(echo)
    create_indices(echo)
    create_triggers(echo)

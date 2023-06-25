from .cozo import client

relation_defs = """
:create embedding_models {
    name: String,
    dimensions: Int,
    requires_instruction: Bool default false,
    provider: String? default null,
}

###

?[name, dimensions, requires_instruction, provider] <- [
    ["e5-base-v2", 768, true, "embaas.io"],
    ["e5-large-v2", 1024, true, "embaas.io"],
]

:put embedding_models {
    name,
    dimensions,
    requires_instruction,
    provider
}

###

:create lm_cache {
    chatml: Json,
    model: String,
    params: Json default {},
    expires_at: Float? default null,
    =>
    response: Json,
    embedding: <F32; 768>
}

###

::hnsw create lm_cache:embedding_space {
    dim: 768,
    m: 50,
    dtype: F32,
    fields: [embedding],
    distance: Cosine,
    ef_construction: 20,
    extend_candidates: false,
    keep_pruned_connections: false,
}

###

:create conceptnet {
    concept_id: Uuid,
    concept: String,
    description: String default "",
    embedding: <F32; 768>,
}

###

::hnsw create conceptnet:embedding_space {
    dim: 768,
    m: 50,
    dtype: F32,
    fields: embedding,
    distance: Cosine,
    ef_construction: 20,
    extend_candidates: false,
    keep_pruned_connections: false,
}

###

::lsh create conceptnet:concept {
    extractor: concept,
    tokenizer: Simple,
    n_perm: 200,
    target_threshold: 0.8,
    n_gram: 3,
    false_positive_weight: 1.0,
    false_negative_weight: 1.0,
}

###

:create entities {
    entity_id: Uuid,
    name: String,
    character_id: Uuid,
    description: String default "",
}

###

:create relations {
    subject: Uuid,
    subject_type: String,
    relation: String,
    object: Uuid,
    object_type: String,
    =>
    weight: Float default 1.0,
}

###

::lsh create entities:name {
    extractor: name,
    tokenizer: Simple,
    n_perm: 200,
    target_threshold: 0.8,
    n_gram: 5,
    false_positive_weight: 1.0,
    false_negative_weight: 1.0,
}

###

:create characters {
    character_id: Uuid,
    updated_at: Validity default [floor(now()), true],
    name: String,
    is_human: Bool default false,
    =>
    about: String default "",
    metadata: Json default {},
    model: String? default null,
}

###

::lsh create characters:name {
    extractor: name,
    tokenizer: Simple,
    n_perm: 50,
    target_threshold: 0.8,
    n_gram: 3,
    false_positive_weight: 1.0,
    false_negative_weight: 1.0,
}

###

:create sessions {
    session_id: Uuid,
    updated_at: Validity default [floor(now()), true],
    =>
    situation: String,
    summary: String? default null,
    metadata: Json default {},
}

###

::fts create sessions:summary {
    extractor: summary,
    extract_filter: !is_null(summary),
    tokenizer: Simple,
    filters: [AsciiFolding, AlphaNumOnly, Lowercase, Stemmer('english'), Stopwords('en')],
}

###

:create session_characters {
    session_id: Uuid,
    character_id: Uuid,
}

###

:create entries {
    session_id: Uuid,
    updated_at: Validity default [floor(now()), true],
    role: String,
    name: String? default null,
    =>
    content: String,
    character_id: Uuid? default null,
    sentiment: Float? default null,
}

###

:create episodes {
    episode_id: Uuid,
    character_id: Uuid,
    last_accessed_at: Validity default [floor(now()), true],
    summary: String,
    =>
    parent_episode: Uuid? default null,
    duration: Float default 0,
    embedding: <F32; 768>,
}

###

::hnsw create episodes:embedding_space {
    dim: 768,
    m: 50,
    dtype: F32,
    fields: [embedding],
    distance: Cosine,
    filter: !is_null(embedding),
    ef_construction: 20,
    extend_candidates: false,
    keep_pruned_connections: false,
}

###

::fts create episodes:summary {
    extractor: summary,
    extract_filter: !is_null(summary),
    tokenizer: Simple,
    filters: [AsciiFolding, AlphaNumOnly, Lowercase, Stemmer('english'), Stopwords('en')],
}

###

:create users {
    email: String,
    character_id: Uuid,
    =>
    assistant_id: Uuid,
}

###

:create beliefs {
    belief_id: Uuid,
    character_id: Uuid,
    last_accessed_at: Validity default [floor(now()), true],
    belief: String,
    =>
    details: String default "",
    parent_belief_id: Uuid? default null,
    valence: Float default 0,
    aspects: [(String, Float, String, String)] default [],
    belief_embedding: <F32; 768>,
    details_embedding: <F32; 768>,
}

###

::hnsw create beliefs:embedding_space {
    dim: 768,
    m: 50,
    dtype: F32,
    fields: [belief_embedding, details_embedding],
    distance: Cosine,
    ef_construction: 20,
    extend_candidates: false,
    keep_pruned_connections: false,
}

###

::fts create beliefs:summary {
    extractor: belief ++ " " ++ details,
    tokenizer: Simple,
    filters: [AsciiFolding, AlphaNumOnly, Lowercase, Stemmer('english'), Stopwords('en')],
}

""".split("###")

def create_all():
    for relation_def in relation_defs:
        print(relation_def)
        client.run(relation_def)
        print("---")
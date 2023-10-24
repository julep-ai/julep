import logging
from memory_api.clients.cozo import client


logger = logging.getLogger(__name__)


def init():
    query = """
    :create beliefs {
        referrent_is_user: Bool,
        referrent_id: Uuid,
        subject_is_user: Bool? default null,
        subject_id: Uuid? default null,
        belief_id: Uuid,
        =>
        belief: String,
        valence: Float default 0.0,
        source_episode: Uuid? default null,
        parent_belief: Uuid? default null,
        sentiment: String default "neutral",
        processed: Bool default false,
        created_at: Float default now(),
        embedding: <F32; 384>,
        fact_embedding: <F32; 1024>? default null,
    }
    """
    idx_query_1 = """
    ::index create beliefs:by_belief_id {
        belief_id,
        belief,
        valence,
        sentiment,
    }
    """
    idx_query_2 = """
    ::index create beliefs:by_parent_belief {
        parent_belief,
        belief_id,
        belief,
        valence,
        sentiment,
    }
    """
    vec_idx_query_1 = """
    ::hnsw create beliefs:embedding_space {
        dim: 384,
        m: 50,
        dtype: F32,
        fields: embedding,
        distance: Cosine,
        ef_construction: 20,
        extend_candidates: true,
        keep_pruned_connections: false,
    }
    """
    vec_idx_query_2 = """
    ::hnsw create beliefs:fact_embedding_space {
        dim: 1536,
        m: 50,
        dtype: F32,
        fields: fact_embedding,
        filter: !is_null(fact_embedding),
        distance: Cosine,
        ef_construction: 20,
        extend_candidates: false,
        keep_pruned_connections: false,
    }
    """
    fts_idx_query = """
    ::fts create beliefs:summary {
        extractor: belief,
        tokenizer: Simple,
        filters: [AsciiFolding, AlphaNumOnly, Lowercase, Stemmer('english'), Stopwords('en')],
    }
    """
    queries = [
        query, 
        idx_query_1, 
        idx_query_2, 
        vec_idx_query_1, 
        vec_idx_query_2, 
        fts_idx_query,
    ]
    
    for query in queries:
        try:
            client.run(query)
        except Exception as e:
            logger.exception(e)

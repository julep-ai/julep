import logging
from memory_api.clients.cozo import client


logger = logging.getLogger(__name__)


def init():
    query = """
    :create episodes {
        referrent_is_user: Bool,
        referrent_id: Uuid,
        subject_is_user: Bool? default null,
        subject_id: Uuid? default null,
        episode_id: Uuid,
        last_accessed_at: Validity default [floor(now()), true],
        =>
        summary: String,
        parent_episode: Uuid? default null,
        happened_at: Float default now(),
        duration: Float default 0,
        importance: Float default 0.5,
        sentiment: String default "neutral",
        sentiment_strength: Float default 0.33334,
        created_at: Float default now(),
        embedding: <F32; 384>,
        fact_embedding: <F32; 1536>? default null,
    }
    """
    idx_query_1 = """
    ::index create episodes:by_episode_id {
        episode_id,
        summary,
        parent_episode,
        happened_at,
        duration,
        importance,
        sentiment,
        sentiment_strength,
        created_at,
    }
    """
    idx_query_2 = """
    ::hnsw create episodes:embedding_space {
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
    vec_idx_query_1 = """
    ::hnsw create episodes:fact_embedding_space {
        dim: 1536,
        m: 50,
        dtype: F32,
        fields: fact_embedding,
        distance: Cosine,
        filter: !is_null(fact_embedding),
        ef_construction: 20,
        extend_candidates: false,
        keep_pruned_connections: false,
    }
    """
    fts_idx_query = """
    ::fts create episodes:summary {
        extractor: summary,
        tokenizer: Simple,
        filters: [AsciiFolding, AlphaNumOnly, Lowercase, Stemmer('english'), Stopwords('en')],
    }
    """
    queries = [
        query, 
        idx_query_1, 
        idx_query_2, 
        vec_idx_query_1, 
        fts_idx_query,
    ]

    try:
        for query in queries:
            client.run(query)
    except Exception as e:
        logger.exception(e)

-- docs_embeddings schema (docs_embeddings is an extended view of docs)
-- +----------------------+--------------------------+-----------+----------+-------------+
-- | Column               | Type                     | Modifiers | Storage  | Description |
-- |----------------------+--------------------------+-----------+----------+-------------|
-- | embedding_uuid       | uuid                     |           | plain    | <null>      |
-- | chunk_seq            | integer                  |           | plain    | <null>      |
-- | chunk                | text                     |           | extended | <null>      |
-- | embedding            | vector(1024)             |           | external | <null>      |
-- | developer_id         | uuid                     |           | plain    | <null>      |
-- | doc_id               | uuid                     |           | plain    | <null>      |
-- | title                | text                     |           | extended | <null>      |
-- | content              | text                     |           | extended | <null>      |
-- | index                | integer                  |           | plain    | <null>      |
-- | modality             | text                     |           | extended | <null>      |
-- | embedding_model      | text                     |           | extended | <null>      |
-- | embedding_dimensions | integer                  |           | plain    | <null>      |
-- | language             | text                     |           | extended | <null>      |
-- | created_at           | timestamp with time zone |           | plain    | <null>      |
-- | updated_at           | timestamp with time zone |           | plain    | <null>      |
-- | metadata             | jsonb                    |           | extended | <null>      |
-- | search_tsv           | tsvector                 |           | extended | <null>      |
-- +----------------------+--------------------------+-----------+----------+-------------+
BEGIN;

-- Create unlogged table for caching embeddings
CREATE UNLOGGED TABLE IF NOT EXISTS embeddings_cache (
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    input_text TEXT NOT NULL,
    input_type TEXT DEFAULT NULL,
    api_key TEXT DEFAULT NULL,
    api_key_name TEXT DEFAULT NULL,
    embedding vector (1024) NOT NULL,
    CONSTRAINT pk_embeddings_cache PRIMARY KEY (provider, model, input_text)
);

-- Add index on provider, model, input_text for faster lookups
CREATE INDEX IF NOT EXISTS idx_embeddings_cache_provider_model_input_text ON embeddings_cache (provider, model, input_text ASC);

-- Add comment explaining table purpose
COMMENT ON TABLE embeddings_cache IS 'Unlogged table that caches embedding requests to avoid duplicate API calls';

CREATE
OR REPLACE function embed_with_cache (
    _provider text,
    _model text,
    _input_text text,
    _input_type text DEFAULT NULL,
    _api_key text DEFAULT NULL,
    _api_key_name text DEFAULT NULL
) returns vector (1024) language plpgsql AS $$

-- Try to get cached embedding first
declare
    cached_embedding vector(1024);
begin
    if _provider != 'voyageai' then
        raise exception 'Only voyageai provider is supported';
    end if;

    select embedding into cached_embedding 
    from embeddings_cache c
    where c.provider = _provider 
    and c.model = _model 
    and c.input_text = _input_text;

    if found then
        return cached_embedding;
    end if;

    -- Not found in cache, call AI embedding function
    cached_embedding := ai.voyageai_embed(
        _model,
        _input_text,
        _input_type,
        _api_key,
        _api_key_name
    );

    -- Cache the result
    insert into embeddings_cache (
        provider,
        model, 
        input_text,
        input_type,
        api_key,
        api_key_name,
        embedding
    ) values (
        _provider,
        _model,
        _input_text, 
        _input_type,
        _api_key,
        _api_key_name,
        cached_embedding
    );

    return cached_embedding;
end;
$$;

COMMIT;

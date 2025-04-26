BEGIN;

-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    api_key_id UUID NOT NULL,
    developer_id UUID NOT NULL,
    api_key_hash TEXT NOT NULL, -- Stores bcrypt hash of the API key
    name TEXT NOT NULL CONSTRAINT ct_api_keys_name_length CHECK (
        length(name) >= 1
        AND length(name) <= 255
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    deleted_at TIMESTAMPTZ,
    CONSTRAINT pk_api_keys PRIMARY KEY (developer_id, api_key_id),
    CONSTRAINT fk_api_keys_developer FOREIGN KEY (developer_id) REFERENCES developers (developer_id),
    CONSTRAINT ct_api_keys_metadata_is_object CHECK (jsonb_typeof(metadata) = 'object')
);

-- Create indexes for api_keys
CREATE INDEX IF NOT EXISTS idx_api_keys_id ON api_keys(api_key_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_developer_id ON api_keys(developer_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_metadata ON api_keys USING GIN(metadata);
CREATE INDEX IF NOT EXISTS idx_api_keys_deleted_at ON api_keys(deleted_at) WHERE deleted_at IS NOT NULL;

-- Add bcrypt hashing function for API keys
CREATE OR REPLACE FUNCTION encrypt_api_key(
    p_api_key TEXT
) RETURNS TEXT AS $$
BEGIN
    RETURN crypt(p_api_key, gen_salt('bf', 10));
END;
$$ LANGUAGE plpgsql 
   SECURITY DEFINER
   SET search_path = pg_catalog, public;

-- Add function to verify API key against stored hash
CREATE OR REPLACE FUNCTION verify_api_key(
    p_api_key TEXT,
    p_hash TEXT
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN p_hash = crypt(p_api_key, p_hash);
END;
$$ LANGUAGE plpgsql 
   SECURITY DEFINER
   SET search_path = pg_catalog, public;

-- Add comment to table
COMMENT ON TABLE api_keys IS 'Stores API keys for developers with bcrypt hashing for security';

COMMIT; 
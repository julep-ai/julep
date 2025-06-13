BEGIN;

-- Create api_keys table with encryption for api_key_encrypted (following secrets pattern)
CREATE TABLE IF NOT EXISTS api_keys (
    api_key_id UUID NOT NULL,
    developer_id UUID NOT NULL,
    api_key_encrypted BYTEA NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    deleted_at TIMESTAMPTZ DEFAULT NULL,
    CONSTRAINT pk_api_keys PRIMARY KEY (developer_id, api_key_id),
    CONSTRAINT uq_api_keys_unique UNIQUE(developer_id, name) WHERE deleted_at IS NULL,
    CONSTRAINT ct_api_keys_metadata_is_object CHECK (jsonb_typeof(metadata) = 'object'),
    CONSTRAINT ct_api_keys_name_valid_identifier CHECK (name ~ '^[a-zA-Z][a-zA-Z0-9_]*$'),
    CONSTRAINT fk_api_keys_developer FOREIGN KEY (developer_id) REFERENCES developers(developer_id)
);

-- Create trigger function for updated_at
CREATE OR REPLACE FUNCTION update_api_keys_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER update_api_keys_timestamp_trigger
BEFORE UPDATE ON api_keys
FOR EACH ROW
EXECUTE FUNCTION update_api_keys_timestamp();

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_api_keys_developer_id ON api_keys(developer_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_name ON api_keys(name);
CREATE INDEX IF NOT EXISTS idx_api_keys_metadata ON api_keys USING gin(metadata);
CREATE INDEX IF NOT EXISTS idx_api_keys_deleted_at ON api_keys(deleted_at) WHERE deleted_at IS NULL;

-- Helper functions for encryption/decryption (following secrets pattern)
CREATE OR REPLACE FUNCTION encrypt_api_key(
    p_value TEXT,
    p_key TEXT
) RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(
        p_value,
        p_key,
        'cipher-algo=aes256'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION decrypt_api_key(
    p_encrypted_value BYTEA,
    p_key TEXT
) RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(
        p_encrypted_value,
        p_key
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add comment to table
COMMENT ON TABLE api_keys IS 'Stores API keys with encryption for developers';

COMMIT; 
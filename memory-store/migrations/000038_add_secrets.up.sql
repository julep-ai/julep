BEGIN;

-- Create secrets table with encryption at rest
CREATE TABLE IF NOT EXISTS secrets (
    secret_id UUID NOT NULL,
    developer_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    value_encrypted BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT pk_secrets PRIMARY KEY (developer_id, agent_id, secret_id),
    CONSTRAINT uq_secrets_unique UNIQUE(developer_id, agent_id, name),
    CONSTRAINT ct_secrets_metadata_is_object CHECK (jsonb_typeof(metadata) = 'object'),
    CONSTRAINT ct_secrets_canonical_name_valid_identifier CHECK (name ~ '^[a-zA-Z][a-zA-Z0-9_]*$')
);

-- Add indexes
CREATE INDEX idx_secrets_developer_id ON secrets(developer_id);
CREATE INDEX idx_secrets_name ON secrets(name);
CREATE INDEX idx_secrets_metadata ON secrets USING gin(metadata);

-- Add encryption/decryption functions using pgcrypto
CREATE OR REPLACE FUNCTION encrypt_secret(
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

CREATE OR REPLACE FUNCTION decrypt_secret(
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

COMMIT; 
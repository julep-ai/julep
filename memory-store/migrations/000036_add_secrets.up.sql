BEGIN;

-- Create secrets table with encryption at rest
CREATE TABLE IF NOT EXISTS secrets (
    secret_id UUID NOT NULL,
    developer_id UUID NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    value_encrypted BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT pk_secrets PRIMARY KEY (developer_id, secret_id),
    CONSTRAINT uq_secrets_unique UNIQUE(developer_id, name),
    CONSTRAINT ct_secrets_canonical_name_valid_identifier CHECK (canonical_name ~ '^[a-zA-Z][a-zA-Z0-9_]*$'),
    CONSTRAINT ct_secrets_metadata_is_object CHECK (jsonb_typeof(metadata) = 'object')
);

-- Add indexes
CREATE INDEX idx_secrets_developer_id ON secrets(developer_id);
CREATE INDEX idx_secrets_name ON secrets(name);
CREATE INDEX idx_secrets_metadata ON secrets USING gin(metadata);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_secrets_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS trg_secrets_updated_at ON secrets;

CREATE TRIGGER trg_secrets_updated_at BEFORE
UPDATE ON secrets FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column ();

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
BEGIN;

-- Create secrets table with encryption at rest
CREATE TABLE IF NOT EXISTS secrets (
    secret_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    developer_id UUID NOT NULL REFERENCES developers(developer_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    value_encrypted BYTEA NOT NULL,
    encryption_key_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(developer_id, name)
);

-- Add RLS policy
ALTER TABLE secrets ENABLE ROW LEVEL SECURITY;

CREATE POLICY access_secrets_policy
    ON secrets
    FOR ALL
    TO postgraphile
    USING (developer_id = current_developer_id())
    WITH CHECK (developer_id = current_developer_id());

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

CREATE TRIGGER update_secrets_updated_at
    BEFORE UPDATE
    ON secrets
    FOR EACH ROW
    EXECUTE FUNCTION update_secrets_updated_at();

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
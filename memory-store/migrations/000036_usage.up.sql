BEGIN;

-- Create usage table to track token usage and costs
CREATE TABLE IF NOT EXISTS usage (
    developer_id UUID NOT NULL,
    model TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL CONSTRAINT ct_usage_prompt_tokens_positive CHECK (prompt_tokens >= 0),
    completion_tokens INTEGER NOT NULL CONSTRAINT ct_usage_completion_tokens_positive CHECK (completion_tokens >= 0),
    cost NUMERIC(10, 6) NOT NULL CONSTRAINT ct_usage_cost_positive CHECK (cost >= 0),
    estimated BOOLEAN NOT NULL DEFAULT FALSE,
    custom_key_used BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT fk_usage_developer FOREIGN KEY (developer_id) REFERENCES developers(developer_id),
    CONSTRAINT ct_metadata_is_object CHECK (jsonb_typeof(metadata) = 'object')
);

-- Convert to hypertable for time-series data
SELECT
    create_hypertable (
        'usage',
        by_range ('created_at', INTERVAL '1 day'),
        if_not_exists => TRUE
    );

SELECT
    add_dimension (
        'usage',
        by_hash ('developer_id', 2),
        if_not_exists => TRUE
    );

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_usage_developer_model ON usage (developer_id, model, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_model ON usage (model, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_metadata ON usage USING GIN (metadata);

-- Add comment to table
COMMENT ON TABLE usage IS 'Tracks token usage and costs by developer and model';

COMMIT;

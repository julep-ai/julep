-- init timescaledb
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS timescaledb_toolkit CASCADE;

-- add timescale's pgai extension
CREATE EXTENSION IF NOT EXISTS vector CASCADE;
CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE;
CREATE EXTENSION IF NOT EXISTS ai CASCADE;

-- add misc extensions (for indexing etc)
CREATE EXTENSION IF NOT EXISTS btree_gin CASCADE;
CREATE EXTENSION IF NOT EXISTS btree_gist CASCADE;
CREATE EXTENSION IF NOT EXISTS citext CASCADE;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" CASCADE;

-- Create function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

COMMENT ON FUNCTION update_updated_at_column() IS 'Trigger function to automatically update updated_at timestamp';

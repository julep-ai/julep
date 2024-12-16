BEGIN;

-- Drop the update_updated_at_column function
DROP FUNCTION IF EXISTS update_updated_at_column ();

-- Drop misc extensions
DROP EXTENSION IF EXISTS "uuid-ossp" CASCADE;

DROP EXTENSION IF EXISTS citext CASCADE;

DROP EXTENSION IF EXISTS btree_gist CASCADE;

DROP EXTENSION IF EXISTS btree_gin CASCADE;

-- Drop timescale's pgai extensions
DROP EXTENSION IF EXISTS ai CASCADE;

DROP EXTENSION IF EXISTS vectorscale CASCADE;

DROP EXTENSION IF EXISTS vector CASCADE;

-- Drop timescaledb extensions
DROP EXTENSION IF EXISTS timescaledb_toolkit CASCADE;

DROP EXTENSION IF EXISTS timescaledb CASCADE;

COMMIT;
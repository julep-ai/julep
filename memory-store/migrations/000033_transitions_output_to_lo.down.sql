BEGIN;

-- Decompress any existing compressed chunks to access all data
SELECT decompress_chunk(c, true) 
FROM show_chunks('transitions') c;

-- Temporarily disable compression
ALTER TABLE transitions SET (timescaledb.compress = false);

-- Create a temporary table to store the mapping between transition_id and JSONB data
CREATE TEMPORARY TABLE transition_output_restore (
    transition_id UUID PRIMARY KEY,
    output_jsonb JSONB
);

-- Retrieve the original JSONB data from large objects and store in the temporary table
DO $$
DECLARE
    r RECORD;
    content BYTEA;
    json_text TEXT;
    fd INTEGER;
BEGIN
    FOR r IN SELECT transition_id, output_oid FROM transitions WHERE output_oid IS NOT NULL LOOP
        -- Get the content of the large object
        fd := lo_open(r.output_oid, 262144);  -- Open for reading (INV_READ = 262144)
        content := loread(fd, 10485760);      -- Read up to 10MB
        PERFORM lo_close(fd);
        
        -- Convert from bytea to text
        json_text := convert_from(content, 'UTF8');
        
        -- Store the JSONB data
        BEGIN
            INSERT INTO transition_output_restore (transition_id, output_jsonb)
            VALUES (r.transition_id, json_text::JSONB);
        EXCEPTION WHEN OTHERS THEN
            -- In case of parsing errors, fall back to an error object
            INSERT INTO transition_output_restore (transition_id, output_jsonb)
            VALUES (r.transition_id, jsonb_build_object('error', 'Failed to restore JSONB from large object'));
        END;
    END LOOP;
END $$;

-- Drop the trigger that manages large objects
DROP TRIGGER IF EXISTS transitions_output_lo_trigger ON transitions;

-- Add the original JSONB column back
ALTER TABLE transitions ADD COLUMN output JSONB;

-- Restore the JSONB data
UPDATE transitions t
SET output = r.output_jsonb
FROM transition_output_restore r
WHERE t.transition_id = r.transition_id;

-- Merge error_info back into output where needed
UPDATE transitions
SET output = output || error_info
WHERE error_info IS NOT NULL;

-- Remove LO OIDs and error_info columns
ALTER TABLE transitions DROP CONSTRAINT IF EXISTS output_oid_fk;
ALTER TABLE transitions DROP COLUMN output_oid;
ALTER TABLE transitions DROP COLUMN error_info;

-- Drop the functions
DROP FUNCTION IF EXISTS get_transition_output;
DROP FUNCTION IF EXISTS set_transition_output;
DROP FUNCTION IF EXISTS get_transition_with_output;

-- Clean up temporary table
DROP TABLE transition_output_restore;

-- Re-enable compression
ALTER TABLE transitions SET (
    timescaledb.compress = TRUE,
    timescaledb.compress_segmentby = 'execution_id',
    timescaledb.compress_orderby = 'created_at DESC, transition_id DESC'
);

-- Drop the index we created
DROP INDEX IF EXISTS idx_transitions_execution_scope_created_at;

COMMIT;
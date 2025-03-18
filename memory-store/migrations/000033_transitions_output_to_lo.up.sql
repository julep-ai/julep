BEGIN;

-- First, ensure the lo extension is available
CREATE EXTENSION IF NOT EXISTS lo;

-- Create a new temporary table to store the mapping between transition_id and lo_oid
CREATE TEMPORARY TABLE transition_output_lo_mapping (
    transition_id UUID PRIMARY KEY,
    output_oid OID,
    original_jsonb JSONB
);

-- Decompress any existing compressed chunks to access all data
SELECT decompress_chunk(c, true) 
FROM show_chunks('transitions') c;

-- Temporarily disable compression
ALTER TABLE transitions SET (timescaledb.compress = false);

-- Store original error information in a temporary column
ALTER TABLE transitions ADD COLUMN error_info JSONB;

-- Extract error information where it exists
UPDATE transitions
SET error_info = 
    CASE 
        WHEN output->>'error' IS NOT NULL THEN jsonb_build_object('error', output->'error') 
        ELSE NULL
    END
WHERE output IS NOT NULL AND output->>'error' IS NOT NULL;

-- Create the lo_manager trigger on transitions table
CREATE TRIGGER transitions_output_lo_trigger
   BEFORE UPDATE OR DELETE ON transitions
   FOR EACH ROW EXECUTE FUNCTION lo_manage(output_oid);

-- We're going to modify the transitions table - add a new column for lo_oid
ALTER TABLE transitions ADD COLUMN output_oid OID;

-- Process each row to convert JSONB to bytea stored in large objects
DO $$
DECLARE
    r RECORD;
    oid OID;
    fd INTEGER;
    data BYTEA;
BEGIN
    FOR r IN SELECT transition_id, output FROM transitions WHERE output IS NOT NULL LOOP
        -- Convert JSONB to bytea
        data := convert_to(r.output::text, 'UTF8');
        
        -- Create a large object
        oid := lo_create(0);
        
        -- Open the large object for writing (INV_WRITE = 131072)
        fd := lo_open(oid, 131072);
        
        -- Write the data (using lowrite instead of lo_write)
        PERFORM lowrite(fd, data);
        
        -- Close the large object
        PERFORM lo_close(fd);
        
        -- Store the mapping for this transition
        INSERT INTO transition_output_lo_mapping (transition_id, output_oid, original_jsonb)
        VALUES (r.transition_id, oid, r.output);
        
        -- Update the transitions table with the new lo_oid
        UPDATE transitions SET output_oid = oid WHERE transition_id = r.transition_id;
    END LOOP;
END $$;

-- Now drop the output column
-- ALTER TABLE transitions DROP COLUMN output;

-- Add constraints and indexes
-- ALTER TABLE transitions ADD CONSTRAINT output_oid_fk FOREIGN KEY (output_oid) REFERENCES pg_largeobject_metadata (oid) ON DELETE SET NULL;

-- Create function to get output as JSONB
CREATE OR REPLACE FUNCTION get_transition_output(oid OID) RETURNS JSONB AS $$
DECLARE
    content BYTEA;
    json_text TEXT;
    fd INTEGER;
BEGIN
    IF oid IS NULL THEN
        RETURN NULL;
    END IF;

    -- Get the content of the large object using alternative method
    -- lo_get is not directly available, so we'll use lo_open/loread/lo_close
    fd := lo_open(oid, 262144);  -- Open for reading (INV_READ = 262144)
    content := loread(fd, 10485760);    -- Read up to 10MB
    PERFORM lo_close(fd);
    
    -- Convert from bytea to text
    json_text := convert_from(content, 'UTF8');
    
    -- Parse as JSON (return NULL for empty objects)
    RETURN CASE 
        WHEN json_text::JSONB = '{}'::JSONB THEN NULL
        ELSE json_text::JSONB
    END;
EXCEPTION
    WHEN OTHERS THEN
        RETURN jsonb_build_object('error', 'Failed to parse large object content as JSON');
END;
$$ LANGUAGE plpgsql;

-- Create function to write output as JSONB
CREATE OR REPLACE FUNCTION set_transition_output(data JSONB) RETURNS OID AS $$
DECLARE
    oid OID;
    fd INTEGER;
    byte_data BYTEA;
BEGIN
    IF data IS NULL THEN
        RETURN NULL;
    END IF;

    -- Convert JSONB to bytea
    byte_data := convert_to(data::text, 'UTF8');
    
    -- Create a large object
    oid := lo_create(0);
    
    -- Open the large object for writing (INV_WRITE = 131072)
    fd := lo_open(oid, 131072);
    
    -- Write the data (using lowrite instead of lo_write)
    PERFORM lowrite(fd, byte_data);
    
    -- Close the large object
    PERFORM lo_close(fd);
    
    RETURN oid;
END;
$$ LANGUAGE plpgsql;

-- Re-enable compression with adjusted segment configuration
ALTER TABLE transitions SET (
    timescaledb.compress = TRUE,
    timescaledb.compress_segmentby = 'execution_id',
    timescaledb.compress_orderby = 'created_at DESC, transition_id DESC'
);

-- Update the query functions to handle the output_oid column
CREATE OR REPLACE FUNCTION get_transition_with_output(tr transitions) RETURNS jsonb AS $$
BEGIN
    RETURN jsonb_build_object(
        'id', tr.transition_id,
        'execution_id', tr.execution_id,
        'created_at', tr.created_at,
        'type', tr.type,
        'step_label', tr.step_label,
        'current_step', tr.current_step,
        'next_step', tr.next_step,
        'output', get_transition_output(tr.output_oid),
        'task_token', tr.task_token,
        'metadata', tr.metadata,
        'error_info', tr.error_info
    );
END;
$$ LANGUAGE plpgsql;

-- Clean up temporary table when done
DROP TABLE transition_output_lo_mapping;

-- Create an index for the common query pattern: execution_id + scope_id + created_at
CREATE INDEX IF NOT EXISTS idx_transitions_execution_scope_created_at 
ON transitions(execution_id, ((current_step).scope_id), created_at);

-- Update existing API views or functions if needed 
-- (This depends on your application's specific access patterns)

COMMIT;
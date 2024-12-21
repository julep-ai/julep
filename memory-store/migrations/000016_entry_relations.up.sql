BEGIN;

-- Create citext extension if not exists
CREATE EXTENSION IF NOT EXISTS citext;

-- Create entry_relations table
CREATE TABLE IF NOT EXISTS entry_relations (
    session_id UUID NOT NULL,
    head UUID NOT NULL,
    relation CITEXT NOT NULL,
    tail UUID NOT NULL,
    is_leaf BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_entry_relations PRIMARY KEY (session_id, head, relation, tail)
);

-- Add foreign key constraint to sessions table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_entry_relations_session'
    ) THEN
        ALTER TABLE entry_relations
        ADD CONSTRAINT fk_entry_relations_session
        FOREIGN KEY (session_id)
        REFERENCES sessions(session_id);
    END IF;
END $$;

-- Create indexes for efficient querying
CREATE INDEX idx_entry_relations_leaf ON entry_relations (session_id, is_leaf);

CREATE OR REPLACE FUNCTION auto_update_leaf_status() RETURNS TRIGGER AS $$
BEGIN
    -- Set is_leaf = false for any existing rows that will now have this new relation as a child
    UPDATE entry_relations 
    SET is_leaf = false
    WHERE session_id = NEW.session_id 
    AND tail = NEW.head;

    -- Set is_leaf for the new row based on whether it has any children
    NEW.is_leaf := NOT EXISTS (
        SELECT 1 
        FROM entry_relations 
        WHERE session_id = NEW.session_id 
        AND head = NEW.tail
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auto_update_leaf_status
BEFORE INSERT OR UPDATE ON entry_relations
FOR EACH ROW
EXECUTE FUNCTION auto_update_leaf_status();

COMMIT;
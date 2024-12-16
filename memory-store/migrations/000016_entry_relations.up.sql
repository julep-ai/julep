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
CREATE INDEX idx_entry_relations_components ON entry_relations (session_id, head, relation, tail);

CREATE INDEX idx_entry_relations_leaf ON entry_relations (session_id, relation, is_leaf);

CREATE
OR REPLACE FUNCTION enforce_leaf_nodes () RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_leaf THEN
        -- Ensure no other relations point to this leaf node as a head
        IF EXISTS (
            SELECT 1 FROM entry_relations 
            WHERE tail = NEW.head AND session_id = NEW.session_id
        ) THEN
            RAISE EXCEPTION 'Cannot assign relations to a leaf node.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_enforce_leaf_nodes BEFORE INSERT
OR
UPDATE ON entry_relations FOR EACH ROW
EXECUTE FUNCTION enforce_leaf_nodes ();

COMMIT;
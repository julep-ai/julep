BEGIN;

-- Add content_hash column to docs table
ALTER TABLE docs ADD COLUMN IF NOT EXISTS content_hash TEXT;

-- Create index on content_hash for fast lookups
CREATE INDEX IF NOT EXISTS idx_docs_content_hash ON docs (developer_id, content_hash);

-- Create a function to generate hash from title and content
CREATE OR REPLACE FUNCTION generate_content_hash(title TEXT, content TEXT) 
RETURNS TEXT AS $$
BEGIN
    -- Use MD5 hash of combined title and content
    -- This provides a good balance between performance and collision avoidance
    RETURN MD5(title || '|' || content);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create trigger function to set content_hash on insert/update
CREATE OR REPLACE FUNCTION docs_update_content_hash() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.content_hash := generate_content_hash(NEW.title, NEW.content);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update content_hash automatically
CREATE TRIGGER trg_docs_content_hash
BEFORE INSERT OR UPDATE OF title, content ON docs
FOR EACH ROW
EXECUTE FUNCTION docs_update_content_hash();

-- Update the content_hash for existing records
UPDATE docs
SET content_hash = generate_content_hash(title, content)
WHERE content_hash IS NULL;

-- Create function to check for duplicate docs by owner BEFORE assigning ownership
CREATE OR REPLACE FUNCTION check_duplicate_doc_owner() 
RETURNS TRIGGER AS $$
DECLARE
    v_content_hash TEXT;
    v_doc_exists BOOLEAN;
BEGIN
    -- First get the content hash of the document being assigned
    SELECT content_hash INTO v_content_hash
    FROM docs
    WHERE developer_id = NEW.developer_id AND doc_id = NEW.doc_id;
    
    -- If we can't find the document, let the insertion proceed
    -- (There should be a foreign key constraint, but it's commented out in the original SQL)
    IF v_content_hash IS NULL THEN
        RETURN NEW;
    END IF;
    
    -- Check if this owner already has a document with the same content hash
    SELECT EXISTS (
        SELECT 1 
        FROM docs d
        JOIN doc_owners o ON d.developer_id = o.developer_id AND d.doc_id = o.doc_id
        WHERE d.developer_id = NEW.developer_id
        AND d.content_hash = v_content_hash
        AND o.owner_type = NEW.owner_type
        AND o.owner_id = NEW.owner_id
        AND o.doc_id != NEW.doc_id  -- Exclude the current document
    ) INTO v_doc_exists;
    
    -- If a document with the same content already exists for this owner, reject the insertion
    IF v_doc_exists THEN
        RAISE EXCEPTION 'Document with similar content already exists for this owner (type: %, id: %)', 
                         NEW.owner_type, NEW.owner_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to check for duplicates when assigning ownership
CREATE TRIGGER trg_check_duplicate_doc_owner
BEFORE INSERT ON doc_owners
FOR EACH ROW
EXECUTE FUNCTION check_duplicate_doc_owner();

COMMIT; 
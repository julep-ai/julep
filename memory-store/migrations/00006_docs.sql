-- Create function to validate language
CREATE OR REPLACE FUNCTION is_valid_language(lang text) 
RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM pg_ts_config WHERE cfgname::text = lang
    );
END;
$$ LANGUAGE plpgsql;

-- Create docs table
CREATE TABLE docs (
    developer_id UUID NOT NULL,
    doc_id UUID NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    index INTEGER NOT NULL,
    modality TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    embedding_dimensions INTEGER NOT NULL,
    language TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    CONSTRAINT pk_docs PRIMARY KEY (developer_id, doc_id),
    CONSTRAINT uq_docs_doc_id_index UNIQUE (doc_id, index),
    CONSTRAINT ct_docs_embedding_dimensions_positive CHECK (embedding_dimensions > 0),
    CONSTRAINT ct_docs_valid_modality CHECK (modality IN ('text', 'image', 'mixed')),
    CONSTRAINT ct_docs_index_positive CHECK (index >= 0),
    CONSTRAINT ct_docs_valid_language 
        CHECK (is_valid_language(language))
);

-- Create sorted index on doc_id (optimized for UUID v7)
CREATE INDEX idx_docs_id_sorted ON docs (doc_id DESC);

-- Create foreign key constraint and index on developer_id
ALTER TABLE docs 
    ADD CONSTRAINT fk_docs_developer 
    FOREIGN KEY (developer_id) 
    REFERENCES developers(developer_id);

CREATE INDEX idx_docs_developer ON docs (developer_id);

-- Create trigger to automatically update updated_at
CREATE TRIGGER trg_docs_updated_at
    BEFORE UPDATE ON docs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment to table
COMMENT ON TABLE docs IS 'Stores document metadata for developers';

-- Create the user_docs table
CREATE TABLE user_docs (
    developer_id UUID NOT NULL,
    user_id UUID NOT NULL,
    doc_id UUID NOT NULL,
    CONSTRAINT pk_user_docs PRIMARY KEY (developer_id, user_id, doc_id),
    CONSTRAINT fk_user_docs_user FOREIGN KEY (developer_id, user_id) REFERENCES users(developer_id, user_id),
    CONSTRAINT fk_user_docs_doc FOREIGN KEY (developer_id, doc_id) REFERENCES docs(developer_id, doc_id)
);

-- Create the agent_docs table
CREATE TABLE agent_docs (
    developer_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    doc_id UUID NOT NULL,
    CONSTRAINT pk_agent_docs PRIMARY KEY (developer_id, agent_id, doc_id),
    CONSTRAINT fk_agent_docs_agent FOREIGN KEY (developer_id, agent_id) REFERENCES agents(developer_id, agent_id),
    CONSTRAINT fk_agent_docs_doc FOREIGN KEY (developer_id, doc_id) REFERENCES docs(developer_id, doc_id)
);

-- Indexes for efficient querying
CREATE INDEX idx_user_docs_user ON user_docs (developer_id, user_id);
CREATE INDEX idx_agent_docs_agent ON agent_docs (developer_id, agent_id);

-- Create a GIN index on the metadata column for efficient searching
CREATE INDEX idx_docs_metadata ON docs USING GIN (metadata);

-- Enable necessary PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS dict_int CASCADE;
CREATE EXTENSION IF NOT EXISTS dict_xsyn CASCADE;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch CASCADE;

-- Configure text search for all supported languages
DO $$
DECLARE
    lang text;
BEGIN
    FOR lang IN (SELECT cfgname FROM pg_ts_config WHERE cfgname IN (
        'arabic', 'danish', 'dutch', 'english', 'finnish', 'french', 
        'german', 'greek', 'hungarian', 'indonesian', 'irish', 'italian',
        'lithuanian', 'nepali', 'norwegian', 'portuguese', 'romanian',
        'russian', 'spanish', 'swedish', 'tamil', 'turkish'
    ))
    LOOP
        -- Configure integer dictionary
        EXECUTE format('ALTER TEXT SEARCH CONFIGURATION %I 
            ALTER MAPPING FOR int, uint WITH intdict', lang);
            
        -- Configure synonym and stemming
        EXECUTE format('ALTER TEXT SEARCH CONFIGURATION %I
            ALTER MAPPING FOR asciihword, hword_asciipart, hword, hword_part, word, asciiword 
            WITH xsyn, %I_stem', lang, lang);
    END LOOP;
END
$$;

-- Add the column (not generated)
ALTER TABLE docs ADD COLUMN search_tsv tsvector;

-- Create function to update tsvector
CREATE OR REPLACE FUNCTION docs_update_search_tsv()
RETURNS trigger AS $$
BEGIN
    NEW.search_tsv :=
        setweight(to_tsvector(NEW.language::regconfig, unaccent(coalesce(NEW.title, ''))), 'A') ||
        setweight(to_tsvector(NEW.language::regconfig, unaccent(coalesce(NEW.content, ''))), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER trg_docs_search_tsv
    BEFORE INSERT OR UPDATE OF title, content, language
    ON docs
    FOR EACH ROW
    EXECUTE FUNCTION docs_update_search_tsv();

-- Create the index
CREATE INDEX idx_docs_search_tsv ON docs USING GIN (search_tsv);

-- Update existing rows (if any)
UPDATE docs SET search_tsv = 
    setweight(to_tsvector(language::regconfig, unaccent(coalesce(title, ''))), 'A') ||
    setweight(to_tsvector(language::regconfig, unaccent(coalesce(content, ''))), 'B');

-- Create GIN trigram indexes for both title and content
CREATE INDEX idx_docs_title_trgm
ON docs USING GIN (title gin_trgm_ops);

CREATE INDEX idx_docs_content_trgm
ON docs USING GIN (content gin_trgm_ops);
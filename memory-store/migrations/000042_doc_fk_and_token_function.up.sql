BEGIN;

ALTER TABLE docs
ADD CONSTRAINT IF NOT EXISTS uq_docs_developer_doc UNIQUE (developer_id, doc_id);

ALTER TABLE doc_owners
ADD CONSTRAINT IF NOT EXISTS fk_doc_owners_doc
FOREIGN KEY (developer_id, doc_id)
REFERENCES docs (developer_id, doc_id) ON DELETE CASCADE;

CREATE OR REPLACE FUNCTION optimized_update_token_count_after () RETURNS TRIGGER AS $$
DECLARE
    calc_token_count INTEGER;
BEGIN
    calc_token_count := cardinality(
        ai.openai_tokenize(
            NEW.model,
            array_to_string(NEW.content::TEXT[], ' ')
        )
    );

    IF calc_token_count <> NEW.token_count THEN
        UPDATE entries
        SET token_count = calc_token_count
        WHERE entry_id = NEW.entry_id;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

COMMIT;

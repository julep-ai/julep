BEGIN;

ALTER TABLE doc_owners
DROP CONSTRAINT IF EXISTS fk_doc_owners_doc;

ALTER TABLE docs
DROP CONSTRAINT IF EXISTS uq_docs_developer_doc;

CREATE OR REPLACE FUNCTION optimized_update_token_count_after () RETURNS TRIGGER AS $$
DECLARE
    calc_token_count INTEGER;
BEGIN
    calc_token_count := cardinality(
        ai.openai_tokenize(
            'gpt-4o',
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

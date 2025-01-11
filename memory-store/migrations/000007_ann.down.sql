BEGIN;

DO $$
DECLARE
    vectorizer_id INTEGER;
BEGIN
    SELECT id INTO vectorizer_id 
    FROM ai.vectorizer 
    WHERE source_table = 'docs';

    -- Drop the vectorizer if it exists
    IF vectorizer_id IS NOT NULL THEN
        PERFORM ai.drop_vectorizer(vectorizer_id, drop_all => true);
    END IF;
END $$;

COMMIT;

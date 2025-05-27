BEGIN;

-- Update token count trigger function to use the model from the new row
CREATE OR REPLACE FUNCTION optimized_update_token_count_after()
RETURNS TRIGGER AS $$
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

-- OPTIONAL: background job for batch token updates
-- SELECT add_job('refresh_entry_token_counts', INTERVAL '5 minutes');

COMMIT;

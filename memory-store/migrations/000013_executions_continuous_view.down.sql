BEGIN;

-- Drop the continuous aggregate policy
DO $$
BEGIN
    BEGIN
        SELECT
            remove_continuous_aggregate_policy ('latest_transitions');
    EXCEPTION
        WHEN others THEN
            RAISE NOTICE 'An error occurred during remove_continuous_aggregate_policy(latest_transitions): %, %', SQLSTATE, SQLERRM;
    END;
END $$;

-- Drop the views
DROP VIEW IF EXISTS latest_executions;

DROP MATERIALIZED VIEW IF EXISTS latest_transitions;

-- Drop the helper function
DROP FUNCTION IF EXISTS to_text (transition_type);

COMMIT;

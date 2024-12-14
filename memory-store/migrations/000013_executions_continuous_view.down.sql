BEGIN;

-- Drop the continuous aggregate policy
SELECT remove_continuous_aggregate_policy('latest_transitions');

-- Drop the views
DROP VIEW IF EXISTS latest_executions;
DROP MATERIALIZED VIEW IF EXISTS latest_transitions;

-- Drop the helper function
DROP FUNCTION IF EXISTS to_text(transition_type);

COMMIT;

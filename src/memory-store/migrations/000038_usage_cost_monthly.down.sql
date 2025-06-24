BEGIN;

-- Remove the continuous aggregate policy
SELECT remove_continuous_aggregate_policy('usage_cost_monthly');

-- Drop the view
DROP VIEW IF EXISTS developer_cost_monthly;

-- Drop the continuous aggregate with CASCADE to remove any dependent objects (like the index)
DROP MATERIALIZED VIEW IF EXISTS usage_cost_monthly CASCADE;

COMMIT; 
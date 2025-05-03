BEGIN;

-- Remove the continuous aggregate policy
SELECT remove_continuous_aggregate_policy('usage_cost_monthly');

-- Drop the view
DROP VIEW IF EXISTS developer_cost_monthly;

-- Drop the continuous aggregate
DROP MATERIALIZED VIEW IF EXISTS usage_cost_monthly;

COMMIT; 
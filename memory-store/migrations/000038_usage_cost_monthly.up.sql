-- Create continuous aggregate for monthly cost per developer with real-time data
CREATE MATERIALIZED VIEW usage_cost_monthly
WITH (timescaledb.continuous, timescaledb.materialized_only=false) AS
SELECT
    developer_id,
    time_bucket('1 month', created_at) AS bucket_start,
    SUM(cost) FILTER (WHERE NOT custom_api_used) AS monthly_cost
FROM usage
GROUP BY developer_id, bucket_start
WITH NO DATA;

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_usage_cost_monthly_developer 
ON usage_cost_monthly (developer_id, bucket_start DESC);

-- Set up continuous aggregate policy to refresh every minute
-- The refresh window must cover at least two buckets (months in this case)
SELECT add_continuous_aggregate_policy(
    'usage_cost_monthly',
    start_offset => INTERVAL '3 months',
    end_offset => INTERVAL '0 minute',
    schedule_interval => INTERVAL '30 seconds'
);

-- Create view that joins with developers table for easy querying
CREATE OR REPLACE VIEW developer_cost_monthly AS
SELECT 
    m.bucket_start,
    d.developer_id,
    d.active,
    d.tags,
    m.monthly_cost
FROM usage_cost_monthly AS m
JOIN developers AS d USING (developer_id); 